import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import List
from utils import (
    create_stats_embed, create_all_stats_embed, create_service_embed, 
    format_duration, create_server_stats_embed, create_graph
)
import config
import json
from views import *

class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.last_run_state = {} 
        self.refresh_service.start()
        self.cleanup_absences.start()

    def cog_unload(self):
        self.refresh_service.cancel()
        self.cleanup_absences.cancel()

    async def get_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        if not data: return 'fr'
        return data['language'] if data.get('language') else 'fr'

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if await self.bot.db.is_blacklisted(str(interaction.user.id)):
                await interaction.response.send_message(config.TRANSLATIONS['fr']['bl_error'], ephemeral=True)
                return False
            return True
        except Exception:
            return True 

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

            for c in configs:
                gid = int(c['guild_id'])
                try:
                    active_sessions = await self.db.get_all_active_sessions(str(gid))
                    is_empty = len(active_sessions) == 0
                    
                    if is_empty and self.last_run_state.get(gid) == "empty":
                        continue
                    
                    await self.bot.update_service_message(gid, c, active_sessions)
                    self.last_run_state[gid] = "empty" if is_empty else "active"

                except discord.NotFound:
                    continue 
                except Exception as e_guild:
                    pass
        except Exception as e:
            print(f"❌ Erreur critique boucle refresh_service: {e}")

    @refresh_service.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    @cleanup_absences.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    async def close_user_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        active_sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        if not active_sessions: return []
        
        choices = []
        for session in active_sessions:
            if current.lower() in session['username'].lower():
                choices.append(app_commands.Choice(name=f"🟢 {session['username']}", value=session['user_id']))
        return choices[:25]

    # --- RDV COMMANDS ---
    @app_commands.command(name="config_rdv", description="Configurer le système de RDV")
    @app_commands.default_permissions(administrator=True)
    async def config_rdv(self, interaction: discord.Interaction):
        conf = await self.db.get_rdv_config(interaction.guild.id)
        types = conf.get('types', [])
        types_str = "\n".join([f"• {t}" for t in types]) if types else "Aucun"
        txt = config.TRANSLATIONS['fr'] 
        embed = discord.Embed(
            title=txt['rdv_setup_title'],
            description=txt['rdv_setup_desc'].format(types=types_str),
            color=config.BOT_COLOR
        )
        await interaction.response.send_message(embed=embed, view=RdvSetupView(self.bot, conf), ephemeral=True)

    # --- ABSENCE ---
    @app_commands.command(name="absence", description="Déclarer une absence")
    async def absence(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        cd = await self.db.get_guild_config(str(interaction.guild_id))
        if cd is None: cd = {}
        raw = cd.get('direction_role_id')
        try: roles = json.loads(raw) if raw else []
        except: roles = [raw] if raw else []
        await interaction.response.send_modal(AbsenceModal(self.bot, lang, roles))

    @app_commands.command(name="absences_list", description="Liste des absences en cours")
    async def absences_list(self, interaction: discord.Interaction):
        absences = await self.db.get_active_absences_details(str(interaction.guild_id))
        embed = discord.Embed(title="📅 Absences en cours", color=config.BOT_COLOR)
        
        if not absences:
            embed.description = "✅ **Aucune absence en cours.**\nTout le monde est disponible (théoriquement)."
            embed.color = discord.Color.green()
        else:
            lines = []
            for abs in absences:
                user_tag = f"<@{abs['user_id']}>"
                lines.append(f"👤 {user_tag} • Fin le : **{abs['end_date']}**")
            embed.description = "\n\n".join(lines)
            embed.set_footer(text=f"Total : {len(absences)} absent(s)")
            
        await interaction.response.send_message(embed=embed, ephemeral=False)

    # --- GENERAL ---
    @app_commands.command(name="feedback", description="Donner un avis ou signaler un bug")
    async def feedback(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        await interaction.response.send_message(view=FeedbackView(self.bot, lang), ephemeral=True)

    @app_commands.command(name="help", description="Menu d'aide")
    async def help(self, interaction: discord.Interaction):
        view = HelpView(self.bot)
        view.update_buttons('lang')
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    @app_commands.command(name="about", description="Infos Bot")
    async def about(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        view = AboutView(self.bot, lang)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="sum", description="Stats perso")
    async def sum(self, interaction: discord.Interaction, user: discord.User = None):
        lang = await self.get_lang(interaction.guild_id)
        target = user or interaction.user
        stats = await self.db.get_user_stats(str(target.id), str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if conf is None: conf = {}
        goal = conf.get('min_hours_goal', 0)
        embed = create_stats_embed(stats, target, lang, goal)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="sumall", description="Classement Global")
    async def sumall(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if conf is None: conf = {}
        goal = conf.get('min_hours_goal', 0)
        absent_users = await self.db.get_absent_users(str(interaction.guild_id))
        embed, pages = create_all_stats_embed(all_stats, interaction.guild, lang, 1, goal, absent_users)
        if pages > 1:
            view = PaginationView(self.bot, all_stats, interaction.guild, lang, goal, absent_users)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="server_stats", description="Stats Serveur")
    @app_commands.default_permissions(administrator=True)
    async def server_stats(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        sessions = await self.db.get_sessions_history(str(interaction.guild_id), 7)
        stats = await self.db.get_advanced_server_stats(str(interaction.guild_id))
        if not sessions or not stats: return await interaction.response.send_message("Pas de données", ephemeral=False)
        view = ServerStatsView(self.bot, interaction.guild_id, sessions, stats, lang)
        file = await create_graph(sessions, "weekly_hours", lang)
        embed = create_server_stats_embed(stats, stats['days_analyzed'], lang)
        await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=False)

    @app_commands.command(name="setup", description="Configuration")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        cd = await self.db.get_guild_config(str(interaction.guild_id))
        if cd is None: cd = {}
        view = SetupView(self.bot, cd)
        lang = cd.get('language', 'fr')
        txt = config.TRANSLATIONS[lang]
        
        desc = txt['setup_panel_desc'] + "\n\n" + view.get_desc(txt)
        embed = discord.Embed(title=txt['setup_panel_title'] + " - Page 1/2", description=desc, color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="edittime", description="Modifier temps")
    @app_commands.default_permissions(manage_guild=True)
    async def edittime(self, interaction: discord.Interaction, user: discord.User):
        lang = await self.get_lang(interaction.guild_id)
        view = EditTimeView(self.bot, lang, user)
        embed = discord.Embed(title="Edit Time", description=f"Cible : {user.display_name}", color=config.BOT_COLOR)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="close", description="Fermer session")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def close(self, interaction: discord.Interaction, user_id: str):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message("Pas en service", ephemeral=True)
        ended = await self.db.end_session(str(user_id), str(interaction.guild_id))
        if ended:
            msg = f"Fermé pour <@{user_id}>. Durée: {format_duration(ended['total_duration'])}"
            await interaction.response.send_message(msg, ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild_id, txt['log_force_close_title'], txt['log_force_close_desc'].format(user=f"<@{user_id}>", admin=interaction.user.mention), config.COLOR_RED, [("Durée", format_duration(ended['total_duration']))])
        else: await interaction.response.send_message("❌ Error", ephemeral=True)

    @app_commands.command(name="pause", description="Pause forcée")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def pause(self, interaction: discord.Interaction, user_id: str):
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        if not session: return await interaction.response.send_message("Pas en service", ephemeral=True)
        if session['is_paused']: 
            await self.db.resume_session(str(user_id), str(interaction.guild_id))
            await interaction.response.send_message("Reprise", ephemeral=True)
            await self.bot.send_log(interaction.guild_id, txt['log_admin_resume_title'], txt['log_admin_resume_desc'].format(admin=interaction.user.mention), config.COLOR_BLUE)
        else: 
            await self.db.pause_session(str(user_id), str(interaction.guild_id))
            await interaction.response.send_message("Pause", ephemeral=True)
            await self.bot.send_log(interaction.guild_id, txt['log_admin_pause_title'], txt['log_admin_pause_desc'].format(admin=interaction.user.mention), config.COLOR_ORANGE)
        await self.bot.update_service_message(interaction.guild_id)

    @app_commands.command(name="forcestart", description="Démarrage forcé")
    @app_commands.default_permissions(manage_guild=True)
    async def forcestart(self, interaction: discord.Interaction, user: discord.User):
        if await self.db.get_active_session(str(user.id), str(interaction.guild_id)): return await interaction.response.send_message("Déjà en service", ephemeral=True)
        await self.db.start_session(str(user.id), str(interaction.guild_id), user.display_name)
        await interaction.response.send_message(f"Démarré pour {user.mention}", ephemeral=True)
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
        await self.db.delete_user_data(str(interaction.guild_id), str(user_id))
        await interaction.response.send_message("Annulé", ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_cancel_title'], txt['log_cancel_desc'].format(user=f"<@{user_id}>", admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="remove_user", description="Supprimer utilisateur")
    @app_commands.default_permissions(administrator=True)
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        await self.db.delete_user_data(str(interaction.guild_id), str(user.id))
        await interaction.response.send_message("Supprimé", ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_remove_title'], txt['log_remove_desc'].format(user=user.mention, admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="reset_server", description="Reset global")
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

    # --- MODIFICATION COMMANDE PRESENCE ---
    @app_commands.command(name="presence", description="Présence")
    @app_commands.default_permissions(administrator=True)
    async def presence(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if channel:
            # On diffère la réponse car le scan peut être long
            await interaction.response.defer(ephemeral=False)
            try:
                target_message = None
                # On scanne les 50 derniers messages pour trouver le plus récent avec des réactions
                async for msg in channel.history(limit=50): 
                    if len(msg.reactions) > 0:
                        target_message = msg
                        break
                
                if not target_message:
                    return await interaction.followup.send("⚠️ Aucun message avec des réactions trouvé dans les 50 derniers messages.", ephemeral=True)

                embed = discord.Embed(title="Présence Réaction", description=f"Analyse du message : {target_message.jump_url}", color=config.BOT_COLOR)
                
                has_reactors = False
                for reaction in target_message.reactions:
                    users = [u.mention async for u in reaction.users()]
                    if users:
                        has_reactors = True
                        val_str = ", ".join(users)
                        # Sécurité longueur embed
                        if len(val_str) > 1020: val_str = val_str[:1015] + "..."
                        embed.add_field(name=str(reaction.emoji), value=val_str, inline=False)
                
                if not has_reactors:
                     return await interaction.followup.send("⚠️ Des réactions existent mais aucun utilisateur trouvé (peut-être des bots ou utilisateurs partis).", ephemeral=True)

                embed.set_footer(text=f"Message du {target_message.created_at.strftime('%d/%m/%Y à %H:%M')}")
                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"❌ Erreur lors de la récupération : {e}", ephemeral=True)
        else:
            active = await self.db.get_all_active_sessions(str(interaction.guild_id))
            embed = create_service_embed(active, interaction.guild, 'fr')
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="pauselist", description="Liste des pauses")
    @app_commands.default_permissions(manage_guild=True)
    async def pauselist(self, interaction: discord.Interaction):
        sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        if not sessions: return await interaction.response.send_message("Personne en pause", ephemeral=False)
        paused = [s for s in sessions if s['is_paused']]
        if not paused: return await interaction.response.send_message("Personne en pause", ephemeral=False)
        desc = "\n".join([f"• <@{s['user_id']}>" for s in paused])
        await interaction.response.send_message(embed=discord.Embed(title="En Pause", description=desc, color=discord.Color.orange()), ephemeral=False)

    @app_commands.command(name="auto_role", description="Donner le rôle auto")
    @app_commands.default_permissions(administrator=True)
    async def auto_role(self, interaction: discord.Interaction, user: discord.Member):
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if not conf or not conf.get('auto_roles_list'): return await interaction.response.send_message("Pas de rôle config", ephemeral=True)
        roles = json.loads(conf['auto_roles_list'])
        for r_id in roles:
            r = interaction.guild.get_role(int(r_id))
            if r: await user.add_roles(r)
        await interaction.response.send_message(f"Rôles donnés à {user.mention}", ephemeral=True)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        await self.bot.send_log(interaction.guild_id, txt['log_autorole_title'], txt['log_autorole_desc'].format(user=user.mention, admin=interaction.user.mention), config.COLOR_GREEN)

    # --- NOUVELLE COMMANDE DELROLE (CORRIGEE) ---
    @app_commands.command(name="delrole", description="Retirer tous les rôles sauf Citoyen")
    @app_commands.default_permissions(manage_guild=True)
    async def delrole(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if not conf or not conf.get('citizen_role_id'):
            return await interaction.followup.send(txt['delrole_error_config'], ephemeral=True)
            
        try:
            cit_role_id = int(conf['citizen_role_id'])
            cit_role = interaction.guild.get_role(cit_role_id)
            
            # Liste des rôles à garder : Citoyen + @everyone + Rôles gérés par intégrations (bots)
            roles_to_keep = [interaction.guild.default_role]
            if cit_role: roles_to_keep.append(cit_role)
            
            # On ajoute les rôles managed (bots) pour éviter les erreurs 403
            for r in user.roles:
                if r.managed:
                    roles_to_keep.append(r)
                    
            # Calcul du nombre de rôles retirés (approximatif)
            removed_count = len(user.roles) - len(set(roles_to_keep) & set(user.roles))
            if removed_count < 0: removed_count = 0
            
            # Si l'utilisateur n'a déjà que ces rôles, on s'arrête
            # On utilise des sets pour comparer les IDs pour être sûr
            current_ids = set(r.id for r in user.roles)
            keep_ids = set(r.id for r in roles_to_keep)
            
            if current_ids.issubset(keep_ids):
                 return await interaction.followup.send(txt['delrole_no_roles'], ephemeral=True)

            await user.edit(roles=list(set(roles_to_keep))) 
            await interaction.followup.send(txt['delrole_success'].format(user=user.mention, count=removed_count), ephemeral=True)
            
            await self.bot.send_log(
                interaction.guild_id, 
                txt['log_delrole_title'], 
                txt['log_delrole_desc'].format(user=user.mention, admin=interaction.user.mention, citizen=cit_role_id), 
                config.COLOR_ORANGE
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: {e}", ephemeral=True)

    @app_commands.command(name="details", description="Détails utilisateur")
    @app_commands.default_permissions(manage_guild=True)
    async def details(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=False)
        sessions = await self.db.get_all_user_sessions(str(user.id), str(interaction.guild_id))
        if not sessions: return await interaction.followup.send("Aucune donnée", ephemeral=False)
        dates = await self.db.get_user_date_range(str(user.id), str(interaction.guild_id))
        first = dates['first'] if dates else None
        last = dates['last'] if dates else None
        view = HistoryPaginationView(sessions, user, first, last, 'fr')
        await interaction.followup.send(embed=view.get_embed(), view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))