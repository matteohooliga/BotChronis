import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import List, Optional
import json
import os
import sys
import asyncio
import csv
from datetime import datetime, timedelta, timezone 
import io

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import config
from utils import (
    create_stats_embed, create_all_stats_embed, create_service_embed, 
    format_duration, create_server_stats_embed, create_graph, generate_transcript_file,
    has_voted_topgg # <-- Ajout de la vérification de vote
)
from views import (
    OMCAccountModal, ServiceButtonsView, LogPaginationView, 
    RdvSetupView, AbsenceModal, FeedbackView, HelpView, 
    AboutView, ServerStatsView, SetupView, EditTimeView,
    HistoryPaginationView, PaginationView, MaintenanceView
)

OMC_GUILD_ID = 1302304936691761234

class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.last_run_state = {} 
        self.refresh_service.start()
        self.cleanup_absences.start()
        self.bot_started = False 

    def cog_unload(self):
        self.refresh_service.cancel()
        self.cleanup_absences.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self.bot_started: return
        self.bot_started = True
        print("🔄 Cogs ServiceCommands chargé.")

    async def get_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        if not data: return 'fr'
        return data['language'] if data.get('language') else 'fr'

    # --- VERIFICATEUR DE COULEUR PREMIUM GLOBALE ---
    async def get_bot_color(self, interaction: discord.Interaction, config_data: dict = None) -> int:
        if not config_data:
            config_data = await self.db.get_guild_config(str(interaction.guild_id))
        if not config_data or not config_data.get('embed_color'):
            return config.BOT_COLOR
            
        is_premium = await self.bot.is_premium(interaction)
        if not is_premium:
            return config.BOT_COLOR
            
        try:
            return int(config_data['embed_color'].lstrip('#'), 16)
        except Exception:
            return config.BOT_COLOR
    # ------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if await self.bot.db.is_blacklisted(str(interaction.user.id)):
                await interaction.response.send_message(config.TRANSLATIONS['fr']['bl_error'], ephemeral=True)
                return False
            return True
        except Exception as e:
            print(f"[ERREUR interaction_check]: {e}")
            return True 

    async def close_user_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        active_sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        if not active_sessions: return []
        choices = []
        for session in active_sessions:
            if current.lower() in session['username'].lower():
                choices.append(app_commands.Choice(name=f"🟢 {session['username']}", value=session['user_id']))
        return choices[:25]

    @tasks.loop(hours=1)
    async def cleanup_absences(self):
        try:
            await self.db.delete_expired_absences()
        except Exception as e:
            print(f"⚠️ Erreur nettoyage absences: {e}")

    @tasks.loop(seconds=10)
    async def refresh_service(self):
        try:
            configs = await self.db.get_all_guild_configs()
            if not configs: return

            # OPTIMISATION : Une seule requête globale pour récupérer toutes les sessions actives
            global_active = await self.db.get_global_active_sessions()
            sessions_by_guild = {}
            if global_active:
                for s in global_active:
                    gid = int(s['guild_id'])
                    if gid not in sessions_by_guild:
                        sessions_by_guild[gid] = []
                    sessions_by_guild[gid].append(s)

            for c in configs:
                gid = int(c['guild_id'])
                try:
                    active_sessions = sessions_by_guild.get(gid, [])
                    is_empty = len(active_sessions) == 0
                    state = ("empty" if is_empty else "active", str(c.get('message_id')))
                    if is_empty and self.last_run_state.get(gid) == state:
                        continue

                    updated = await self.bot.update_service_message(gid, c, active_sessions)
                    if updated:
                        self.last_run_state[gid] = state

                except discord.NotFound: 
                    continue 
                except Exception as e: 
                    print(f"[ERREUR refresh_service guilde {gid}]: {e}")
        except Exception as e: 
            print(f"❌ Erreur critique boucle refresh_service: {e}")

    @refresh_service.before_loop
    async def before_refresh(self): await self.bot.wait_until_ready()

    @cleanup_absences.before_loop
    async def before_cleanup(self): await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        try:
            conf = await self.db.get_rdv_config(guild.id)
            if not conf: return
        except Exception as e: 
            print(f"[ERREUR on_member_remove fetch conf]: {e}")
            return

        target_topic_str = f"Patient: {member.id}"
        for channel in guild.text_channels:
            if channel.topic and target_topic_str in channel.topic:
                try: await self._auto_close_ticket(channel, member, conf)
                except Exception as e: print(f"❌ Erreur auto-close: {e}")

    async def _auto_close_ticket(self, channel, member, conf):
        reason = "Le membre a quitté le serveur (Fermeture Automatique)."
        topic = channel.topic or ""
        staff_id = None
        staff_msg_id = None
        
        try:
            parts = topic.split("|")
            for p in parts:
                if "Staff:" in p: staff_id = int(p.split(":")[1].strip())
                if "Msg:" in p: staff_msg_id = int(p.split(":")[1].strip())
        except Exception as e: 
            print(f"[ERREUR parsing topic ticket]: {e}")

        transcript_file = await generate_transcript_file(channel, self.bot.user, reason)
        
        try:
            embed_dm = discord.Embed(title="Ticket Fermé", color=discord.Color.red())
            embed_dm.description = f"Votre ticket sur le serveur **{channel.guild.name}** a été fermé automatiquement car vous avez quitté le serveur."
            embed_dm.add_field(name="Raison", value=reason, inline=False)
            embed_dm.set_footer(text=config.EMBED_FOOTER)
            transcript_file.fp.seek(0)
            await member.send(embed=embed_dm, file=transcript_file)
        except Exception: 
            pass # L'utilisateur n'accepte pas les MP

        if staff_msg_id and conf.get('staff'):
            try:
                chan_staff = channel.guild.get_channel(int(conf['staff']))
                if chan_staff:
                    msg = await chan_staff.fetch_message(staff_msg_id)
                    new_embed = msg.embeds[0]
                    new_embed.color = discord.Color.dark_grey()
                    new_embed.set_footer(text=f"Fermeture Auto (Leave) le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
                    await msg.edit(content=f"🚫 **Membre Parti** (Ticket fermé auto)", embed=new_embed, view=None)
            except Exception as e: 
                print(f"[ERREUR maj panel staff]: {e}")

        transcript_id = conf.get('transcript')
        if transcript_id:
            try:
                log_chan = channel.guild.get_channel(int(transcript_id))
                if log_chan:
                    embed_log = discord.Embed(title="🚪 Ticket Fermé (Départ)", color=discord.Color.dark_grey())
                    pat_men = f"{member.name} ({member.id})" 
                    stf_men = f"<@{staff_id}>" if staff_id else "Inconnu"
                    embed_log.description = f"Le ticket de **{pat_men}** a été fermé automatiquement car il a quitté le serveur."
                    embed_log.add_field(name="Ouvert par (Staff)", value=stf_men, inline=True)
                    embed_log.add_field(name="Raison", value=reason, inline=False)
                    embed_log.timestamp = datetime.now()
                    transcript_file.fp.seek(0)
                    await log_chan.send(embed=embed_log, file=transcript_file)
            except Exception as e: 
                print(f"[ERREUR logs transcript]: {e}")

        await asyncio.sleep(2) 
        try: await channel.delete(reason="Auto-close: Member left guild")
        except Exception as e: print(f"[ERREUR channel delete]: {e}")

    # ==========================================================================
    # COMMANDES SLASH
    # ==========================================================================

    @app_commands.command(name="config_rdv", description="Configurer le système RDV")
    @app_commands.default_permissions(administrator=True)
    async def config_rdv(self, interaction: discord.Interaction):
        conf = await self.db.get_rdv_config(interaction.guild.id)
        types = conf.get('types', [])
        bot_color = await self.get_bot_color(interaction)
        txt = config.TRANSLATIONS['fr'] 
        
        embed = discord.Embed(
            title=txt['rdv_setup_title'],
            description=txt['rdv_setup_desc'].format(types="\n".join([f"• {t}" for t in types]) if types else "Aucun"),
            color=bot_color
        )
        await interaction.response.send_message(embed=embed, view=RdvSetupView(self.bot, conf), ephemeral=True)

    @app_commands.command(name="absence", description="Déclarer une absence")
    async def absence(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        cd = await self.db.get_guild_config(str(interaction.guild_id))
        bot_color = await self.get_bot_color(interaction, cd)
        
        if cd is None: cd = {}
        raw = cd.get('direction_role_id')
        try: roles = json.loads(raw) if raw else []
        except Exception: roles = [raw] if raw else []
        await interaction.response.send_modal(AbsenceModal(self.bot, lang, roles, bot_color))

    @app_commands.command(name="absences_list", description="Liste des absences en cours")
    async def absence_list(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        absences = await self.db.get_active_absences_details(str(interaction.guild_id))
        bot_color = await self.get_bot_color(interaction)
        
        embed = discord.Embed(title=txt['abs_list_title'], color=bot_color)
        
        if not absences:
            embed.description = txt['abs_list_empty']
            embed.color = discord.Color.green()
        else:
            lines = []
            for abs in absences:
                try:
                    start_dt = datetime.strptime(abs['start_date'], "%d/%m/%Y")
                    end_dt = datetime.strptime(abs['end_date'], "%d/%m/%Y")
                    start_ts = int(start_dt.timestamp())
                    end_ts = int(end_dt.timestamp())
                    date_display = f"📅 Du <t:{start_ts}:D> au <t:{end_ts}:D> (<t:{end_ts}:R>)"
                except ValueError:
                    date_display = f"📅 {abs['start_date']} - {abs['end_date']}"

                line = (
                    f"👤 <@{abs['user_id']}>\n"
                    f"{date_display}\n"
                    f"{txt['abs_reason_title'].format(reason=abs['reason'])}"
                )
                lines.append(line)

            chunked_desc = ""
            for line in lines:
                if len(chunked_desc) + len(line) > 3500:
                    chunked_desc += txt['msg_truncated']
                    break
                chunked_desc += line + "\n────────────────────\n"
            
            embed.description = chunked_desc
            embed.set_footer(text=txt['abs_footer'].format(count=len(absences)))
            
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="feedback", description="Avis ou Bug")
    async def feedback(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        await interaction.response.send_message(view=FeedbackView(self.bot, lang), ephemeral=True)

    @app_commands.command(name="help", description="Menu d'aide")
    async def help(self, interaction: discord.Interaction):
        bot_color = await self.get_bot_color(interaction)
        show_partner = bool(interaction.guild_id) and not await self.bot.is_premium(interaction)
        view = HelpView(self.bot, bot_color, show_partner=show_partner)
        view.update_buttons('lang')
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    @app_commands.command(name="about", description="Infos Bot")
    async def about(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        bot_color = await self.get_bot_color(interaction)
        show_partner = bool(interaction.guild_id) and not await self.bot.is_premium(interaction)
        view = AboutView(self.bot, lang, bot_color, show_partner=show_partner)
        embed = view.get_embed()

        now = datetime.now(timezone.utc)
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        
        ts = int(target.timestamp())
        
        txt = config.TRANSLATIONS[lang]
        msg_warning = "⚠️ Toutes les sessions actives sont fermées automatiquement." if lang == 'fr' else "⚠️ All active sessions are closed automatically."
        val_str = f"🕒 **<t:{ts}:t>**\n{msg_warning}"
        
        embed.add_field(name=txt.get('about_maint_title', "🔄 Maintenance"), value=val_str, inline=False)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="vote", description="Voter pour le bot")
    async def vote(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        view = discord.ui.View()
        btn = discord.ui.Button(label=txt.get('btn_vote', "Voter"), url=config.VOTE_LINK, style=discord.ButtonStyle.link)
        view.add_item(btn)
        await interaction.response.send_message(txt.get('vote_msg', "Cliquez pour voter :"), view=view, ephemeral=True)

    @app_commands.command(name="sum", description="Stats perso")
    async def sum(self, interaction: discord.Interaction, user: discord.User = None):
        lang = await self.get_lang(interaction.guild_id)
        target = user or interaction.user
        absent_users = await self.db.get_absent_users(str(interaction.guild_id))
        stats = await self.db.get_user_stats(str(target.id), str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if conf is None: conf = {}
        
        bot_color = await self.get_bot_color(interaction, conf)
        embed = create_stats_embed(stats, target, lang, conf.get('min_hours_goal', 0), bot_color)
        if str(target.id) in absent_users: embed.title = f"{embed.title} 🚫 (Absent)"
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="sumall", description="Classement Global")
    async def sumall(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if conf is None: conf = {}
        absent_users = await self.db.get_absent_users(str(interaction.guild_id))
        
        bot_color = await self.get_bot_color(interaction, conf)
        embed, pages = create_all_stats_embed(all_stats, interaction.guild, lang, 1, conf.get('min_hours_goal', 0), absent_users, bot_color)
        
        view = PaginationView(self.bot, all_stats, interaction.guild, lang, conf.get('min_hours_goal', 0), absent_users, bot_color)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @app_commands.command(name="server_stats", description="Stats Serveur")
    @app_commands.default_permissions(administrator=True)
    async def server_stats(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        sessions = await self.db.get_sessions_history(str(interaction.guild_id), 7)
        stats = await self.db.get_advanced_server_stats(str(interaction.guild_id))
        if not sessions or not stats: return await interaction.response.send_message("Pas de données", ephemeral=False)
        
        bot_color = await self.get_bot_color(interaction)
        view = ServerStatsView(self.bot, interaction.guild_id, sessions, stats, lang, bot_color)
        file = await create_graph(sessions, "weekly_hours", lang)
        embed = create_server_stats_embed(stats, stats['days_analyzed'], lang, bot_color)
        
        await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=False)

    @app_commands.command(name="setup", description="Configuration")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        cd = await self.db.get_guild_config(str(interaction.guild_id))
        if cd is None: cd = {}
        
        is_premium = await self.bot.is_premium(interaction)
        bot_color = await self.get_bot_color(interaction, cd)

        view = SetupView(self.bot, cd, is_premium)
        lang = cd.get('language', 'fr')
        txt = config.TRANSLATIONS[lang]
        desc = txt['setup_panel_desc'] + "\n\n" + view.get_desc(txt)
        
        embed = discord.Embed(title=txt['setup_panel_title'] + " - Page 1/3", description=desc, color=bot_color)
        embed.set_footer(text=config.EMBED_FOOTER)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="edittime", description="Modifier le temps")
    @app_commands.default_permissions(manage_guild=True)
    async def edittime(self, interaction: discord.Interaction, user: discord.User):
        lang = await self.get_lang(interaction.guild_id)
        bot_color = await self.get_bot_color(interaction)
        
        view = EditTimeView(self.bot, lang, user, bot_color)
        embed = discord.Embed(title="Edit Time", description=f"Cible : {user.display_name}", color=bot_color)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="close", description="Fermer une session")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def close(self, interaction: discord.Interaction, user_id: str):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message("Pas en service", ephemeral=True)
        
        ended = await self.db.end_session(str(user_id), str(interaction.guild_id))
        if ended:
            embed = discord.Embed(title="🛑 Session Fermée (Force Close)", color=discord.Color.dark_red())
            embed.description = f"Session de <@{user_id}> fermée par {interaction.user.mention}."
            embed.add_field(name="✅ Temps", value=f"`{format_duration(ended['total_duration'])}`", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild_id, txt['log_force_close_title'], txt['log_force_close_desc'].format(user=f"<@{user_id}>", admin=interaction.user.mention), config.COLOR_RED, [("Durée", format_duration(ended['total_duration']))])
        else: await interaction.response.send_message("❌ Error", ephemeral=True)

    @app_commands.command(name="pause", description="Mettre en pause")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def pause(self, interaction: discord.Interaction, user_id: str):
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        if not session: return await interaction.response.send_message("Pas en service", ephemeral=True)
        
        if session['is_paused']: 
            await self.db.resume_session(str(user_id), str(interaction.guild_id))
            embed = discord.Embed(title="▶️ Reprise Forcée", description=f"Session de <@{user_id}> réactivée par {interaction.user.mention}.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, txt['log_admin_resume_title'], txt['log_admin_resume_desc'].format(admin=interaction.user.mention), config.COLOR_BLUE)
        else: 
            await self.db.pause_session(str(user_id), str(interaction.guild_id))
            embed = discord.Embed(title="⏸️ Pause Forcée", description=f"Session de <@{user_id}> mise en pause par {interaction.user.mention}.", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, txt['log_admin_pause_title'], txt['log_admin_pause_desc'].format(admin=interaction.user.mention), config.COLOR_ORANGE)
        await self.bot.update_service_message(interaction.guild_id)

    @app_commands.command(name="forcestart", description="Forcer le début")
    @app_commands.default_permissions(manage_guild=True)
    async def forcestart(self, interaction: discord.Interaction, user: discord.User):
        if await self.db.get_active_session(str(user.id), str(interaction.guild_id)): return await interaction.response.send_message("Déjà en service", ephemeral=True)
        await self.db.start_session(str(user.id), str(interaction.guild_id), user.display_name)
        embed = discord.Embed(title="🟢 Service Démarré (Force Start)", description=f"Session démarrée pour {user.mention} par {interaction.user.mention}.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_admin_start_title'], txt['log_admin_start_desc'].format(user=user.mention, admin=interaction.user.mention), config.COLOR_GREEN)

    @app_commands.command(name="cancel", description="Annuler session")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def cancel(self, interaction: discord.Interaction, user_id: str):
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message("Pas en service", ephemeral=True)
        await self.db.cancel_active_session(session['id'])
        embed = discord.Embed(title="🗑️ Session Annulée", description=f"La session de <@{user_id}> a été annulée et supprimée par {interaction.user.mention}.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_cancel_title'], txt['log_cancel_desc'].format(user=f"<@{user_id}>", admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="remove_user", description="Supprimer les données")
    @app_commands.default_permissions(administrator=True)
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        await self.db.delete_user_data(str(interaction.guild_id), str(user.id))
        embed = discord.Embed(title="🗑️ Données Supprimées", description=f"Toutes les sessions de {user.mention} ont été effacées par {interaction.user.mention}.", color=discord.Color.dark_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_remove_title'], txt['log_remove_desc'].format(user=user.mention, admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="reset_server", description="Réinitialisation globale")
    @app_commands.choices(periode=[app_commands.Choice(name="Semaine", value="week"), app_commands.Choice(name="Mois", value="month"), app_commands.Choice(name="Tout", value="all")])
    @app_commands.default_permissions(administrator=True)
    async def reset_server(self, interaction: discord.Interaction, periode: app_commands.Choice[str]):
        ms = None
        if periode.value == "week": ms = 7 * 86400000
        elif periode.value == "month": ms = 30 * 86400000
        deleted = await self.db.reset_guild_data(str(interaction.guild_id), ms)
        await self.bot.update_service_message(interaction.guild_id)
        await interaction.response.send_message(f"Reset effectué ({deleted} sessions)", ephemeral=True)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_reset_title'], txt['log_reset_desc'].format(admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="presence", description="Agents en service ou recensement des réactions")
    @app_commands.default_permissions(administrator=True)
    async def presence(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        if channel is None:
            await self._show_service_presence(interaction)
        else:
            await self._show_reaction_presence(interaction, channel)

    @app_commands.command(name="reaction_list", description="Voir les réactions")
    @app_commands.default_permissions(administrator=True)
    async def reaction_list(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._show_reaction_presence(interaction, channel)

    async def _show_reaction_presence(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=False)
        lang = await self.get_lang(interaction.guild_id)
        bot_color = await self.get_bot_color(interaction)
        txt = config.TRANSLATIONS[lang]
        
        try:
            absent_users = await self.db.get_absent_users(str(interaction.guild_id))
            target_message = None
            async for msg in channel.history(limit=50): 
                if len(msg.reactions) > 0:
                    target_message = msg
                    break
            if not target_message:
                return await interaction.followup.send(txt['pres_no_react_msg'], ephemeral=True)
            embed = discord.Embed(title=txt['pres_title'], description=txt['pres_desc'].format(url=target_message.jump_url), color=bot_color)
            has_reactors = False
            for reaction in target_message.reactions:
                list_present = []
                list_absent = []
                async for u in reaction.users():
                    if str(u.id) in absent_users: list_absent.append(u.mention)
                    else: list_present.append(u.mention)
                if list_present or list_absent:
                    has_reactors = True
                    val_str = ""
                    if list_present: val_str += ", ".join(list_present)
                    else: val_str += "*(Aucun membre actif)*"
                    if list_absent:
                        val_str += f"\n\n🚫 **Absents ({len(list_absent)}) :**\n"
                        val_str += ", ".join(list_absent)
                    if len(val_str) > 1020: val_str = val_str[:1015] + "..."
                    count_total = len(list_present) + len(list_absent)
                    embed.add_field(name=f"{str(reaction.emoji)} ({count_total})", value=val_str, inline=False)
            if not has_reactors:
                    return await interaction.followup.send(txt['pres_no_users'], ephemeral=True)
            date_str = target_message.created_at.strftime('%d/%m/%Y %H:%M')
            embed.set_footer(text=txt['pres_footer'].format(date=date_str))
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    @app_commands.command(name="service_list", description="Liste des agents")
    @app_commands.default_permissions(administrator=True)
    async def service_list(self, interaction: discord.Interaction):
        await self._show_service_presence(interaction)

    async def _show_service_presence(self, interaction: discord.Interaction):
        active = await self.db.get_all_active_sessions(str(interaction.guild_id))
        lang = await self.get_lang(interaction.guild_id)
        embed = create_service_embed(active, interaction.guild, lang)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="pauselist", description="Agents en pause")
    @app_commands.default_permissions(manage_guild=True)
    async def pauselist(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        if not sessions: return await interaction.response.send_message(txt['pause_list_empty'], ephemeral=False)
        paused = [s for s in sessions if s['is_paused']]
        if not paused: return await interaction.response.send_message(txt['pause_list_empty'], ephemeral=False)
        desc = "\n".join([f"• <@{s['user_id']}>" for s in paused])
        await interaction.response.send_message(embed=discord.Embed(title=txt['pause_list_title'], description=desc, color=discord.Color.orange()), ephemeral=False)

    @app_commands.command(name="auto_role", description="Donner rôles auto")
    @app_commands.default_permissions(administrator=True)
    async def auto_role(self, interaction: discord.Interaction, user: discord.Member):
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if not conf or not conf.get('auto_roles_list'): return await interaction.response.send_message("Pas de rôle config", ephemeral=True)
        roles = json.loads(conf['auto_roles_list'])
        for r_id in roles:
            r = interaction.guild.get_role(int(r_id))
            if r: await user.add_roles(r)
        now_ts = int(datetime.now().timestamp())
        try: await self.db.set_employee_date(str(interaction.guild_id), str(user.id), now_ts)
        except Exception: pass
        await interaction.response.send_message(f"Rôles donnés à {user.mention}", ephemeral=True)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_autorole_title'], txt['log_autorole_desc'].format(user=user.mention, admin=interaction.user.mention), config.COLOR_GREEN)

    @app_commands.command(name="employees", description="Liste des employés")
    @app_commands.default_permissions(manage_guild=True)
    async def employees(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        
        bot_color = await self.get_bot_color(interaction, conf)
        
        if not conf or not conf.get('auto_roles_list'): return await interaction.followup.send(txt['emp_no_config'], ephemeral=True)
        try:
            role_ids = json.loads(conf['auto_roles_list'])
            if not role_ids: return await interaction.followup.send(txt['emp_list_empty'], ephemeral=True)
            guild = interaction.guild
            target_roles = []
            roles_str = []
            for r_id in role_ids:
                r = guild.get_role(int(r_id))
                if r: 
                    target_roles.append(r)
                    roles_str.append(r.mention)
            if not target_roles: return await interaction.followup.send(txt['emp_roles_not_found'], ephemeral=True)
            found_members = []
            for m in guild.members:
                if not m.bot and any(tr in m.roles for tr in target_roles): found_members.append(m)
            if not found_members: return await interaction.followup.send(txt['emp_no_members'].format(roles=', '.join(roles_str)), ephemeral=True)
            try: dates_map = await self.db.get_employees_dates(str(interaction.guild_id))
            except Exception: dates_map = {}
            
            embed = discord.Embed(title=txt['emp_title'].format(count=len(found_members)), color=bot_color)
            base_desc = txt['emp_roles_target'].format(roles=', '.join(roles_str))
            lines = []
            is_en = (lang == 'en')
            txt_since = "Since" if is_en else "Depuis le"
            txt_na = "N/A"
            def sort_key(member):
                date_bdd = dates_map.get(str(member.id), 0)
                if date_bdd > 0: return date_bdd
                return member.joined_at.timestamp() if member.joined_at else 0
            found_members.sort(key=sort_key)
            for m in found_members:
                ts_bdd = dates_map.get(str(m.id))
                if ts_bdd: date_display = f"<t:{ts_bdd}:d>"
                else: date_display = txt_na
                lines.append(f"• {m.mention} (`{m.name}`) • {txt_since} {date_display}")
            chunked_desc = ""
            for line in lines:
                if len(chunked_desc) + len(line) > 3500:
                    chunked_desc += txt['msg_truncated']
                    break
                chunked_desc += line + "\n"
            embed.description = base_desc.rstrip() + f"\n{chunked_desc}"
            footer_txt = config.EMBED_FOOTER + (" | Dates based on auto_role" if is_en else " | Dates basées sur auto_role")
            embed.set_footer(text=footer_txt)
            await interaction.followup.send(embed=embed)
        except Exception as e: await interaction.followup.send(f"❌ Error : {e}", ephemeral=True)

    @app_commands.command(name="delrole", description="Retirer rôles")
    @app_commands.default_permissions(manage_guild=True)
    async def delrole(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if not conf or not conf.get('citizen_role_id'): return await interaction.followup.send(txt['delrole_error_config'], ephemeral=True)
        try:
            cit_role_id = int(conf['citizen_role_id'])
            cit_role = interaction.guild.get_role(cit_role_id)
            roles_to_keep = [interaction.guild.default_role]
            if cit_role: roles_to_keep.append(cit_role)
            for r in user.roles:
                if r.managed: roles_to_keep.append(r)
            removed_count = len(user.roles) - len(set(roles_to_keep) & set(user.roles))
            if removed_count < 0: removed_count = 0
            current_ids = set(r.id for r in user.roles)
            keep_ids = set(r.id for r in roles_to_keep)
            if current_ids.issubset(keep_ids): return await interaction.followup.send(txt['delrole_no_roles'], ephemeral=True)
            await user.edit(roles=list(set(roles_to_keep))) 
            await interaction.followup.send(txt['delrole_success'].format(user=user.mention, count=removed_count), ephemeral=True)
            await self.bot.send_log(interaction.guild_id, txt['log_delrole_title'], txt['log_delrole_desc'].format(user=user.mention, admin=interaction.user.mention, citizen=cit_role_id), config.COLOR_ORANGE)
        except Exception as e: await interaction.followup.send(f"❌ Erreur: {e}", ephemeral=True)

    @app_commands.command(name="details", description="Détails et historique des sessions")
    @app_commands.default_permissions(manage_guild=True)
    async def details(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=False)
        sessions = await self.db.get_all_user_sessions(str(user.id), str(interaction.guild_id))
        
        if not sessions: 
            return await interaction.followup.send("Aucune donnée pour cet utilisateur.", ephemeral=False)
            
        dates = await self.db.get_user_date_range(str(user.id), str(interaction.guild_id))
        first = dates['first'] if dates else None
        last = dates['last'] if dates else None
        
        bot_color = await self.get_bot_color(interaction)
        view = HistoryPaginationView(sessions, user, first, last, 'fr', bot_color)
        await interaction.followup.send(embed=view.get_embed(), view=view)

    @app_commands.command(name="premium", description="⭐ Débloquez le plein potentiel de Chronis !")
    async def premium(self, interaction: discord.Interaction):
        is_premium = await self.bot.is_premium(interaction)

        if is_premium:
            embed = discord.Embed(
                title="💎 Chronis Premium Actif !",
                description=(
                    "Merci pour votre soutien ! Ce serveur bénéficie actuellement de toutes les fonctionnalités Premium.\n\n"
                    "Profitez des exports automatiques, des rôles dynamiques, des limites débloquées et de l'absence de publicité partenaire."
                ),
                color=0xFFD700
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            return await interaction.response.send_message(embed=embed, ephemeral=False)

        embed = discord.Embed(
            title="🚀 Propulsez votre serveur avec Chronis Premium !",
            description=(
                "L'abonnement Premium débloque des outils de gestion automatisés pour votre structure.\n\n"
                "💎 **Un seul abonnement profite à tout le serveur !**"
            ),
            color=0x2ecc71
        )
        
        embed.add_field(name="📊 Analytics Comparatifs", value="Rapport hebdo avec calcul automatique de la progression de l'activité (%).", inline=False)
        embed.add_field(name="🔔 Relances Anti-Inactivité", value="Envoie un MP automatique aux agents n'ayant pas atteint leur quota 24h avant la purge.", inline=False)
        embed.add_field(name="🏷️ Automatisation des Rôles", value="Attribue/Retire un rôle Discord automatiquement lors des services.", inline=False)
        embed.add_field(name="📥 Rapports & Exports (.CSV)", value="Recevez vos bilans Excel automatiquement dans vos logs.", inline=False)
        embed.add_field(name="⏰ Purges & Couleurs", value="Choisissez votre moment de reset et la couleur du bot.", inline=False)
        embed.add_field(name="📅 RDV Illimités", value="Fini les restrictions ! Créez autant de motifs que souhaité.", inline=False)
        embed.add_field(name="🚨 Personnalisation & Alertes", value="Couleurs custom et alertes DEFCON sur-mesure.", inline=False)
        embed.add_field(name="🔕 Sans publicité partenaire", value="Aucune promotion Hosterfy affichée dans `/about` ou après la configuration du serveur.", inline=False)
        
        embed.set_footer(text="Soutenez le développement et passez au niveau supérieur ! 💖")

        class PremiumView(MaintenanceView):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(sku_id=config.PREMIUM_SKU_ID))

        await interaction.response.send_message(embed=embed, view=PremiumView(), ephemeral=True)

    @app_commands.command(name="export", description="💎 [PREMIUM/VOTE] Exporter toutes les statistiques en format Excel (.csv)")
    @app_commands.default_permissions(administrator=True)
    async def export_stats(self, interaction: discord.Interaction):
        is_premium = await self.bot.is_premium(interaction)
        
        if not is_premium:
            try:
                has_voted = await has_voted_topgg(str(interaction.user.id))
            except Exception:
                has_voted = False
                
            if not has_voted:
                embed = discord.Embed(
                    title="⭐ Exportation : Premium ou Vote",
                    description=(
                        "L'exportation des données en un clic est une fonctionnalité Avancée.\n\n"
                        "Pour l'utiliser **gratuitement**, soutenez-nous en votant pour le bot sur Top.gg ! "
                        "Cela débloquera l'exportation pour vous pendant 12 heures.\n\n"
                        "👉 Découvrez l'abonnement `/premium` pour lever cette limite à vie."
                    ),
                    color=0xFFD700
                )
                class UnlockView(MaintenanceView):
                    def __init__(self):
                        super().__init__(timeout=None)
                        self.add_item(discord.ui.Button(label="Voter & Débloquer", url=config.VOTE_LINK, emoji="🗳️"))
                        self.add_item(discord.ui.Button(label="Passer Premium", sku_id=config.PREMIUM_SKU_ID))
                return await interaction.response.send_message(embed=embed, view=UnlockView(), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        
        if not all_stats:
            return await interaction.followup.send("⚠️ Aucune donnée d'activité n'est enregistrée pour le moment.", ephemeral=True)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', dialect='excel') 
        
        writer.writerow(['ID Utilisateur', 'Nom / Pseudo', 'Total Sessions', 'Temps Total (Formaté)', 'Temps Total (Millisecondes)'])

        for s in all_stats:
            formatted_time = format_duration(s['total_time'] or 0)
            writer.writerow([
                s['user_id'], 
                s['username'], 
                s['total_sessions'], 
                formatted_time, 
                s['total_time'] or 0
            ])

        output.seek(0)
        file_data = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        date_str = datetime.now().strftime("%Y-%m-%d")
        discord_file = discord.File(fp=file_data, filename=f"Export_Chronis_{date_str}.csv")

        await interaction.followup.send(
            content="✅ **Exportation réussie !** Voici le rapport d'activité complet de votre serveur :", 
            file=discord_file, 
            ephemeral=True
        )
        
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, "📁 Exportation CSV", f"{interaction.user.mention} a exporté les données du serveur.", config.COLOR_BLUE)

    @app_commands.command(name="defcon", description="💎 [PREMIUM] Diffuser une alerte d'urgence à la population")
    @app_commands.choices(niveau=[
        app_commands.Choice(name="🔴 DEFCON 1 (Alerte Maximale / Évacuation)", value=1),
        app_commands.Choice(name="🟠 DEFCON 2 (Alerte Critique / Déploiement)", value=2),
        app_commands.Choice(name="🟡 DEFCON 3 (Alerte Renforcée / Mobilisation)", value=3),
        app_commands.Choice(name="🟢 DEFCON 4 (Alerte Légère / Vigilance)", value=4),
        app_commands.Choice(name="🔵 DEFCON 5 (Situation Normale / Paix)", value=5),
    ])
    @app_commands.default_permissions(administrator=True)
    async def defcon(self, interaction: discord.Interaction, niveau: app_commands.Choice[int], message: str, titre_personnalise: str = None, image_url: str = None, role_a_mentionner: discord.Role = None):
        is_premium = await self.bot.is_premium(interaction)
        if not is_premium:
            embed = discord.Embed(
                title="⭐ Fonctionnalité Premium",
                description="Le système de transmission d'alerte globale (DEFCON) est exclusif à **Chronis Premium**.\n\nUtilisez `/premium` pour vous abonner !",
                color=0xFFD700
            )
            class UpgradeView(MaintenanceView):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(sku_id=config.PREMIUM_SKU_ID))
            return await interaction.response.send_message(embed=embed, view=UpgradeView(), ephemeral=True)

        colors = {
            1: 0xFF0000, 
            2: 0xFF4500, 
            3: 0xFFFF00, 
            4: 0x00FF00, 
            5: 0x0000FF  
        }
        
        titre = titre_personnalise if titre_personnalise else f"🚨 TRANSMISSION D'URGENCE : {niveau.name.split(' (')[0]}"
        
        embed = discord.Embed(title=titre, description=f"**MESSAGE OFFICIEL :**\n\n{message}", color=colors[niveau.value])
        
        if image_url:
            try: embed.set_image(url=image_url)
            except Exception: pass
            
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Alerte déclenchée par {interaction.user.display_name} • Système DEFCON", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)
        
        content = role_a_mentionner.mention if role_a_mentionner else ""
        
        await interaction.response.send_message("✅ Alerte diffusée avec succès !", ephemeral=True)
        await interaction.channel.send(content=content, embed=embed)        

async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))
