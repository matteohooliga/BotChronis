import discord
from discord.ui import View, Modal, TextInput, button
import config
import json
import sys
import io
import aiohttp
import csv
import re
from datetime import datetime, timedelta

# Import des utilitaires
from utils import (
    format_duration, check_permissions, create_all_stats_embed, 
    create_graph, create_server_stats_embed, create_service_embed,
    generate_transcript_file 
)

async def global_maintenance_allows(interaction, lang='fr'):
    bot = interaction.client
    if not getattr(bot, 'maintenance_mode', False) or str(interaction.user.id) == str(config.OWNER_ID):
        return True
    text = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])['maint_block_msg']
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)
    return False


class MaintenanceView(discord.ui.View):
    async def interaction_check(self, interaction):
        return await global_maintenance_allows(interaction, getattr(self, 'lang', 'fr'))


class MaintenanceModal(discord.ui.Modal):
    async def interaction_check(self, interaction):
        return await global_maintenance_allows(interaction, getattr(self, 'lang', 'fr'))


# --- CONFIGURATION API OMC ---
OMC_API_URL = "https://votre-site-web.com/api/create_account" 
OMC_API_KEY = "votre_cle_api_secrete"

# --- FONCTION UTILITAIRE (LOGS FEEDBACK DEV) ---
async def send_feedback_log(bot, interaction, title, color, fields):
    target_id = config.DEV_FEEDBACK_CHANNEL_ID
    channel = bot.get_channel(target_id)
    
    if channel is None:
        try:
            channel = await bot.fetch_channel(target_id)
        except Exception as e:
            print(f"[ERREUR] send_feedback_log fetch: {e}")
            return False
            
    if channel:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
            
        embed.add_field(name="Source", value=f"{interaction.guild.name} (`{interaction.guild.id}`)", inline=False)
        embed.set_footer(text=config.EMBED_FOOTER)
        
        role_mention = f"<@&{config.DEV_FEEDBACK_ROLE_ID}>"
        try:
            await channel.send(content=role_mention, embed=embed)
            return True
        except Exception as e:
            print(f"[ERREUR] send_feedback_log send: {e}")
            return False
    return False

# ==============================================================================
#                 PAGINATION POUR TEXTE (Pour la commande +infos)
# ==============================================================================

class LogPaginationView(MaintenanceView):
    def __init__(self, data_list, title="Informations", items_per_page=10):
        super().__init__(timeout=60)
        self.data_list = data_list
        self.title = title
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = (len(data_list) - 1) // items_per_page + 1

    def create_embed(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        current_data = self.data_list[start:end]
        
        description_text = "\n".join(current_data)
        
        embed = discord.Embed(title=self.title, description=description_text, color=discord.Color.blue())
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages} • Total: {len(self.data_list)}")
        return embed

    def update_buttons(self):
        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page == self.total_pages - 1)

    @button(label="◀️", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

# ==============================================================================
#                            MODALES (FORMULAIRES)
# ==============================================================================

class OMCAccountModal(MaintenanceModal, title="Création de compte OMC"):
    identity = discord.ui.TextInput(label="Nom et Prénom", placeholder="Ex: Dupont Jean", required=True, max_length=100)
    dob = discord.ui.TextInput(label="Date de naissance", placeholder="JJ/MM/AAAA", required=True, max_length=15)
    job = discord.ui.TextInput(label="Profession", placeholder="Ex: Médecin, Policier...", required=True, max_length=100)
    username_id = discord.ui.TextInput(label="Identifiant (ID)", placeholder="Votre nom d'utilisateur pour le site", required=True, max_length=50)
    password = discord.ui.TextInput(label="Mot de passe", placeholder="Choisissez un mot de passe", required=True, min_length=6, max_length=100, style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        payload = {
            "full_name": self.identity.value, "dob": self.dob.value, "profession": self.job.value,
            "username": self.username_id.value, "password": self.password.value,
            "discord_id": str(interaction.user.id), "discord_tag": interaction.user.name
        }
        try:
            if "votre-site-web.com" in OMC_API_URL:
                 await interaction.followup.send(f"✅ (Mode Test) Compte demandé pour **{self.identity.value}**.", ephemeral=True)
                 return
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json", "Authorization": OMC_API_KEY}
                async with session.post(OMC_API_URL, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        await interaction.followup.send(f"✅ **Compte créé avec succès !**\nBienvenue, {self.identity.value}.", ephemeral=True)
                    elif response.status == 409:
                        await interaction.followup.send("⚠️ **Erreur :** Cet Identifiant/ID existe déjà sur le site.", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ **Erreur du site web** (Code {response.status}). Contactez un administrateur.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR] API OMC: {e}")
            await interaction.followup.send("❌ Impossible de contacter le site web. Veuillez réessayer plus tard.", ephemeral=True)

class ReviewModal(MaintenanceModal):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_review_title'])
        self.subject = discord.ui.TextInput(label=texts['feedback_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.rating = discord.ui.TextInput(label=texts['fb_review_rating'], style=discord.TextStyle.short, placeholder="5", required=True, max_length=1)
        self.comment = discord.ui.TextInput(label=texts['fb_review_comment'], style=discord.TextStyle.paragraph, required=True, max_length=1000)
        self.add_item(self.subject)
        self.add_item(self.rating)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            stars = max(1, min(5, int(self.rating.value)))
            star_str = "⭐" * stars
        except ValueError:
            star_str = "❓"
        fields = [
            ("📌 Sujet", f"**{self.subject.value}**"),
            (texts['fb_field_rating'], f"{star_str} ({self.rating.value}/5)"),
            ("💬 Commentaire", self.comment.value)
        ]
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_review_title'], config.COLOR_ORANGE, fields)
        if success:
            await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else:
            await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class BugReportModal(MaintenanceModal):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_bug_title'])
        self.subject = discord.ui.TextInput(label=texts['fb_bug_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.description = discord.ui.TextInput(label=texts['fb_bug_desc'], style=discord.TextStyle.paragraph, required=True, max_length=2000)
        self.media = discord.ui.TextInput(label=texts['fb_bug_media'], style=discord.TextStyle.short, required=False, placeholder="https://...")
        self.add_item(self.subject)
        self.add_item(self.description)
        self.add_item(self.media)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        fields = [
            ("📌 Sujet", f"**{self.subject.value}**"),
            ("📝 Description", self.description.value)
        ]
        if self.media.value:
            fields.append((texts['fb_field_media'], self.media.value))
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_bug_title'], config.COLOR_RED, fields)
        if success:
            await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else:
            await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class AbsenceModal(MaintenanceModal):
    def __init__(self, bot, lang, direction_role_id, bot_color=config.BOT_COLOR):
        self.bot = bot
        self.lang = lang
        self.direction_role_id = direction_role_id
        self.bot_color = bot_color
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['abs_modal_title'])
        self.start_date = discord.ui.TextInput(label=texts['abs_start_label'], placeholder="JJ/MM/AAAA", max_length=10, required=True)
        self.end_date = discord.ui.TextInput(label=texts['abs_end_label'], placeholder="JJ/MM/AAAA", max_length=10, required=True)
        self.reason = discord.ui.TextInput(label=texts['abs_reason_label'], style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.start_date)
        self.add_item(self.end_date)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            d1 = datetime.strptime(self.start_date.value, "%d/%m/%Y")
            d2 = datetime.strptime(self.end_date.value, "%d/%m/%Y")
            if d2 < d1:
                return await interaction.response.send_message(texts['abs_error_logic'], ephemeral=True)
            
            days = (d2 - d1).days
            if days == 0: days = 1
            duration_str = f"{days} jour(s)" if self.lang == 'fr' else f"{days} day(s)"
            
            embed = discord.Embed(title=texts['abs_embed_title'].format(user=interaction.user.display_name), color=self.bot_color, timestamp=datetime.now())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name=texts['abs_user_field'], value=interaction.user.mention, inline=False)
            embed.add_field(name=texts['abs_field_dates'], value=f"📅 {self.start_date.value} ➔ {self.end_date.value}", inline=False)
            embed.add_field(name=texts['abs_field_duration'], value=f"⏱️ {duration_str}", inline=True)
            embed.add_field(name=texts['abs_field_reason'], value=f"📝 {self.reason.value}", inline=False)
            embed.set_footer(text=config.EMBED_FOOTER)
            
            content = ""
            if self.direction_role_id:
                try:
                    roles = json.loads(self.direction_role_id) if isinstance(self.direction_role_id, str) else self.direction_role_id
                    if isinstance(roles, int): roles = [str(roles)]
                    elif isinstance(roles, list): roles = [str(r) for r in roles]
                    content = " ".join([f"<@&{r}>" for r in roles if r])
                except Exception:
                    content = f"<@&{self.direction_role_id}>"
            
            try:
                msg = await interaction.channel.send(content=content, embed=embed)
            except discord.Forbidden:
                return await interaction.response.send_message("❌ **Erreur :** Permission manquante.", ephemeral=True)
            except Exception as e:
                print(f"[ERREUR] Absence send message: {e}")
                return await interaction.response.send_message("❌ Erreur inconnue lors de l'envoi.", ephemeral=True)
            
            await self.bot.db.add_absence(str(interaction.user.id), interaction.user.display_name, str(interaction.guild_id), self.start_date.value, self.end_date.value, self.reason.value, str(msg.id))
            await msg.edit(view=AbsenceView(self.bot, self.lang))
            try: await msg.add_reaction("✅")
            except discord.NotFound: pass
            except Exception as e: print(f"[ERREUR] Absence add reaction: {e}")
            
            await interaction.response.send_message("✅", ephemeral=True)
        except ValueError:
            await interaction.response.send_message(texts['abs_error_format'], ephemeral=True)

class EditTimeModal(MaintenanceModal):
    def __init__(self, bot, lang, target_user, operation, bot_color=config.BOT_COLOR):
        texts = config.TRANSLATIONS[lang]
        op_text = texts['time_added'] if operation == "add" else texts['time_removed']
        super().__init__(title=op_text)
        self.bot = bot
        self.lang = lang
        self.target_user = target_user
        self.operation = operation
        self.bot_color = bot_color
        
        self.hours = discord.ui.TextInput(label=texts['et_label_hours'], placeholder="0", required=False, default="0", max_length=3)
        self.minutes = discord.ui.TextInput(label=texts['et_label_minutes'], placeholder="0", required=False, default="0", max_length=2)
        self.seconds = discord.ui.TextInput(label=texts['et_label_seconds'], placeholder="0", required=False, default="0", max_length=2)
        self.add_item(self.hours)
        self.add_item(self.minutes)
        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            h = int(self.hours.value) if self.hours.value else 0
            m = int(self.minutes.value) if self.minutes.value else 0
            s = int(self.seconds.value) if self.seconds.value else 0
            
            total_sec = (h * 3600) + (m * 60) + s
            if total_sec <= 0: return await interaction.response.send_message(texts['error_invalid_input'], ephemeral=True)
            
            ms_diff = total_sec * 1000 * (1 if self.operation == "add" else -1)
            old_stats = await self.bot.db.get_user_stats(str(self.target_user.id), str(interaction.guild_id))
            old_total = format_duration(old_stats['total_time'] if old_stats else 0)
            
            await self.bot.db.add_time_adjustment(str(self.target_user.id), str(interaction.guild_id), self.target_user.display_name, ms_diff)
            new_stats = await self.bot.db.get_user_stats(str(self.target_user.id), str(interaction.guild_id))
            new_total = format_duration(new_stats['total_time'] or 0)
            
            action_str = texts['time_added'] if self.operation == "add" else texts['time_removed']
            val_fmt = format_duration(total_sec * 1000)
            
            embed = discord.Embed(title=texts['edit_success'].format(user=self.target_user.display_name, action="", value="", new_total="").split('\n')[0], color=self.bot_color)
            embed.description = texts['edit_desc'].format(user=self.target_user.mention)
            embed.add_field(name=texts['edit_field_action'], value=action_str, inline=True)
            embed.add_field(name=texts['edit_field_amount'], value=f"`{val_fmt}`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name=texts['edit_field_old'], value=f"`{old_total}`", inline=True)
            embed.add_field(name="➡️", value=" ", inline=True)
            embed.add_field(name=texts['edit_field_new_total'], value=f"`{new_total}`", inline=True)
            embed.set_footer(text=config.EMBED_FOOTER)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_edit_time_title'], texts['log_edit_time_desc'].format(admin=interaction.user.mention), config.COLOR_BLUE, [(texts['edit_field_target'], self.target_user.mention), (texts['edit_field_action'], action_str), (texts['edit_field_amount'], val_fmt), (texts['edit_field_new_total'], new_total)])
        except Exception as e:
            print(f"[ERREUR] EditTime on_submit: {e}")
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class GoalModal(MaintenanceModal):
    def __init__(self, parent_view, txt, is_premium=False):
        super().__init__(title=txt['setup_ph_goal'][:45])
        self.view = parent_view
        self.txt = txt
        self.is_premium = is_premium
        
        val = str(int(parent_view.sel_goal / 3600000)) if parent_view.sel_goal else ""
        self.goal = discord.ui.TextInput(
            label="Objectif d'heures / Goal (0 = OFF)", 
            placeholder="Ex: 10", 
            required=True, 
            default=val
        )
        self.add_item(self.goal)
        
        if self.is_premium:
            val_time = str(parent_view.sel_purge_time) if parent_view.sel_purge_time else "00:00"
            self.purge_time_input = discord.ui.TextInput(
                label="Heure de purge (ex: 23:30)", 
                placeholder="HH:MM", 
                required=False, 
                default=val_time,
                max_length=5
            )
            self.add_item(self.purge_time_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.is_premium and not await interaction.client.is_premium(interaction):
            return await interaction.response.send_message(
                '❌ Le droit Chronis Premium de ce serveur a changé. Relancez `/setup` pour enregistrer la configuration.',
                ephemeral=True
            )
        try:
            ms_goal = int(self.goal.value) * 3600000
        except ValueError:
            ms_goal = 0
            
        if self.is_premium and hasattr(self, 'purge_time_input') and self.purge_time_input.value:
            pt = self.purge_time_input.value.strip()
            if re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', pt):
                if len(pt) == 4: 
                    pt = "0" + pt
                self.view.sel_purge_time = pt
            else:
                await interaction.response.send_message("❌ Erreur : L'heure de purge doit être au format `HH:MM` (ex: `14:30`). L'enregistrement a été annulé, veuillez recommencer.", ephemeral=True)
                return
                
        await interaction.response.defer()
        guild = interaction.guild
        
        try:
            chan_svc = guild.get_channel(int(self.view.sel_service))
            chan_log = guild.get_channel(int(self.view.sel_logs)) if self.view.sel_logs else None
            
            role_dir = json.dumps(self.view.sel_role) if self.view.sel_role else None
            role_auto = json.dumps(self.view.sel_autorole) if self.view.sel_autorole else None
            role_cit = str(self.view.sel_citizen) if self.view.sel_citizen else None 
            role_service = str(self.view.sel_service_role) if self.view.sel_service_role else None
            embed_color = str(self.view.sel_color) if self.view.sel_color else None
            
            day_int = int(self.view.sel_purge_day) if self.view.sel_purge_day is not None else -1
            time_str = str(self.view.sel_purge_time) if self.view.sel_purge_time else "00:00"
            
            embed = create_service_embed([], guild, self.view.sel_lang)
            view = ServiceButtonsView(self.view.bot, self.view.sel_lang)
            
            msg = None
            if self.view.sel_service: 
                 msg = await chan_svc.send(embed=embed, view=view)
            
            await self.view.bot.db.set_guild_config(
                str(guild.id), 
                str(chan_svc.id) if chan_svc else None, 
                str(msg.id) if msg else None, 
                str(chan_log.id) if chan_log else None, 
                self.view.sel_lang, 
                role_dir, 
                ms_goal, 
                role_auto,
                role_cit,
                role_service,
                embed_color
            )
            
            await self.view.bot.db.set_auto_purge(str(guild.id), day_int, time_str)
            
            if chan_log:
                try: await chan_log.send(embed=discord.Embed(title=self.txt['log_setup_title'], description=self.txt['log_setup_desc'], color=config.COLOR_GREEN))
                except Exception as e: print(f"[ERREUR] GoalModal send log: {e}")
                
            confirmation = self.txt['setup_success'].format(channel=chan_svc.mention)
            if self.view.first_setup and not await self.view.bot.is_premium(interaction):
                if self.view.sel_lang == 'en':
                    partner_offer = (f'🌐 Partner offer: 5% off Hosterfy hosting with code '
                                     f'**CHRONISBOT** — {config.AFFILIATE_LINK}')
                else:
                    partner_offer = f'{config.AFFILIATE_TEXT}\n{config.AFFILIATE_LINK}'
                confirmation += f'\n\n{partner_offer}'
            await interaction.followup.send(confirmation, ephemeral=True)
            self.view.stop()
        except Exception as e:
            print(f"[ERREUR] GoalModal submit: {e}")
            await interaction.followup.send(f"❌ Erreur: `{e}`", ephemeral=True)

class SetupView(MaintenanceView):
    def __init__(self, bot, config_data=None, is_premium=False):
        super().__init__(timeout=300)
        self.bot = bot
        self.is_premium = is_premium
        self.first_setup = not bool(config_data)
        self.page = 1 
        self.sel_lang = config_data.get('language','fr') if config_data else 'fr'
        self.sel_service = config_data.get('channel_id') if config_data else None
        self.sel_logs = config_data.get('log_channel_id') if config_data else None
        self.sel_role = json.loads(config_data.get('direction_role_id') or '[]') if config_data else []
        self.sel_autorole = json.loads(config_data.get('auto_roles_list') or '[]') if config_data else []
        self.sel_citizen = config_data.get('citizen_role_id') if config_data else None
        self.sel_service_role = config_data.get('service_role_id') if config_data else None
        self.sel_color = config_data.get('embed_color') if config_data else None
        self.sel_purge_day = config_data.get('auto_purge_day', -1) if config_data else -1
        self.sel_purge_time = config_data.get('auto_purge_time', '00:00') if config_data else '00:00'
        self.sel_goal = config_data.get('min_hours_goal',0) if config_data else 0
        self.update_components()
        
    def update_components(self):
        self.clear_items()
        t = config.TRANSLATIONS[self.sel_lang]
        
        if self.page == 1:
            b1 = discord.ui.Button(label="FR", custom_id="fr", style=discord.ButtonStyle.primary if self.sel_lang=='fr' else discord.ButtonStyle.secondary)
            b1.callback = self.cb_fr
            self.add_item(b1)
            b2 = discord.ui.Button(label="EN", custom_id="en", style=discord.ButtonStyle.primary if self.sel_lang=='en' else discord.ButtonStyle.secondary)
            b2.callback = self.cb_en
            self.add_item(b2)
            
            self.add_item(discord.ui.ChannelSelect(placeholder="📢 Définir Salon Service", channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="svc"))
            self.add_item(discord.ui.ChannelSelect(placeholder="📜 Définir Salon Logs", channel_types=[discord.ChannelType.text], min_values=0, max_values=1, custom_id="log"))
            
            color_options = [
                discord.SelectOption(label="Classique (Violet)", value="#6100bd", emoji="🟣"),
                discord.SelectOption(label="Rouge", value="#E74C3C", emoji="🔴"),
                discord.SelectOption(label="Bleu", value="#3498DB", emoji="🔵"),
                discord.SelectOption(label="Vert", value="#2ECC71", emoji="🟢"),
                discord.SelectOption(label="Orange", value="#E67E22", emoji="🟠"),
                discord.SelectOption(label="Noir", value="#000000", emoji="⚫"),
                discord.SelectOption(label="Blanc", value="#FFFFFF", emoji="⚪")
            ]
            self.add_item(discord.ui.Select(placeholder="🎨 Définir Couleur (Premium)", min_values=0, max_values=1, custom_id="color", options=color_options))
            
            btn_next = discord.ui.Button(label=t['setup_btn_next'], custom_id="next", style=discord.ButtonStyle.primary, row=4)
            btn_next.callback = self.cb_next
            self.add_item(btn_next)

        elif self.page == 2:
            self.add_item(discord.ui.RoleSelect(placeholder="👔 Définir Rôle Direction", min_values=0, max_values=20, custom_id="role"))
            self.add_item(discord.ui.RoleSelect(placeholder="🏆 Définir Rôle Auto", min_values=0, max_values=20, custom_id="autorole"))
            self.add_item(discord.ui.RoleSelect(placeholder="👤 Définir Rôle Citoyen", min_values=0, max_values=1, custom_id="citizen"))
            self.add_item(discord.ui.RoleSelect(placeholder="💎 Rôle 'En Service' (Premium)", min_values=0, max_values=1, custom_id="servicerole"))

            btn_back = discord.ui.Button(label=t['setup_btn_back'], custom_id="back", style=discord.ButtonStyle.secondary, row=4)
            btn_back.callback = self.cb_back
            self.add_item(btn_back)
            
            btn_next = discord.ui.Button(label=t['setup_btn_next'], custom_id="next_2", style=discord.ButtonStyle.primary, row=4)
            btn_next.callback = self.cb_next_2
            self.add_item(btn_next)

        elif self.page == 3:
            day_options = [
                discord.SelectOption(label="Désactivé (Purge Manuelle)", value="-1", emoji="❌"),
                discord.SelectOption(label="Lundi", value="0", emoji="📅"),
                discord.SelectOption(label="Mardi", value="1", emoji="📅"),
                discord.SelectOption(label="Mercredi", value="2", emoji="📅"),
                discord.SelectOption(label="Jeudi", value="3", emoji="📅"),
                discord.SelectOption(label="Vendredi", value="4", emoji="📅"),
                discord.SelectOption(label="Samedi", value="5", emoji="📅"),
                discord.SelectOption(label="Dimanche", value="6", emoji="📅")
            ]
            self.add_item(discord.ui.Select(placeholder="💎 Jour de Purge Auto (Premium)", min_values=0, max_values=1, custom_id="purgeday", options=day_options))
            
            btn_back = discord.ui.Button(label=t['setup_btn_back'], custom_id="back_2", style=discord.ButtonStyle.secondary, row=4)
            btn_back.callback = self.cb_back_2
            self.add_item(btn_back)

            btn_save = discord.ui.Button(label=t['setup_btn_save'], custom_id="save", style=discord.ButtonStyle.success, row=4)
            btn_save.callback = self.cb_save
            self.add_item(btn_save)
        
    async def refresh(self, i):
        t = config.TRANSLATIONS[self.sel_lang]
        title = f"{t['setup_panel_title']} - Page {self.page}/3"
        base_desc = t.get(f'setup_panel_desc_{self.page}', "")
            
        full_desc = f"{base_desc}\n\n{self.get_summary_string()}"
        
        current_color = config.BOT_COLOR
        if self.sel_color:
            try: current_color = int(self.sel_color.lstrip('#'), 16)
            except ValueError: pass
            
        e = discord.Embed(title=title, description=full_desc, color=current_color)
        e.set_footer(text=config.EMBED_FOOTER)
        
        if i.response.is_done():
            await i.edit_original_response(embed=e, view=self)
        else:
            await i.response.edit_message(embed=e, view=self)
            
    def get_desc(self, txt):
        return self.get_summary_string()
        
    def get_summary_string(self):
        svc = f"<#{self.sel_service}>" if self.sel_service else "❌ *Non défini*"
        log = f"<#{self.sel_logs}>" if self.sel_logs else "❌ *Non défini*"
        
        rol_count = len(self.sel_role) if isinstance(self.sel_role, list) else (1 if self.sel_role else 0)
        roles_str = f"✅ {rol_count} rôle(s)" if rol_count > 0 else "❌ *Non défini*"

        aut_count = len(self.sel_autorole) if isinstance(self.sel_autorole, list) else (1 if self.sel_autorole else 0)
        aut_str = f"✅ {aut_count} rôle(s)" if aut_count > 0 else "❌ *Non défini*"

        cit = f"<@&{self.sel_citizen}>" if self.sel_citizen else "❌ *Non défini*"
        serv_role = f"<@&{self.sel_service_role}>" if self.sel_service_role else "❌ *Non défini*" 
        color_display = self.sel_color if self.sel_color else "Par défaut (Violet)"
        
        days_map = {"-1": "❌ Désactivé", "0": "Lundi", "1": "Mardi", "2": "Mercredi", "3": "Jeudi", "4": "Vendredi", "5": "Samedi", "6": "Dimanche"}
        day_str = str(self.sel_purge_day)
        purge_time_disp = self.sel_purge_time if self.sel_purge_time else "À définir"
        purge_str = f"{days_map.get(day_str, '❌ Désactivé')} à {purge_time_disp}" if day_str != "-1" else "❌ Désactivée"
        
        flag = "🇫🇷" if self.sel_lang == 'fr' else "🇬🇧"
        
        return (
            f"**📊 CONFIGURATION ACTUELLE**\n"
            f"> **Langue :** {flag} `{self.sel_lang.upper()}`\n"
            f"> **Salon Service :** {svc}\n"
            f"> **Salon Logs :** {log}\n"
            f"> **Rôle Direction :** {roles_str}\n"
            f"> **Rôle Auto :** {aut_str}\n"
            f"> **Rôle Citoyen :** {cit}\n"
            f"> **💎 Rôle 'En Service' :** {serv_role}\n"
            f"> **💎 Couleur :** {color_display}\n"
            f"> **💎 Purge Hebdomadaire :** {purge_str}"
        )
        
    async def cb_fr(self, i): self.sel_lang='fr'; self.update_components(); await self.refresh(i)
    async def cb_en(self, i): self.sel_lang='en'; self.update_components(); await self.refresh(i)
    async def cb_next(self, i): self.page = 2; self.update_components(); await self.refresh(i)
    async def cb_back(self, i): self.page = 1; self.update_components(); await self.refresh(i)
    async def cb_next_2(self, i): self.page = 3; self.update_components(); await self.refresh(i)
    async def cb_back_2(self, i): self.page = 2; self.update_components(); await self.refresh(i)
    async def cb_save(self, i):
        t=config.TRANSLATIONS[self.sel_lang]
        await i.response.send_modal(GoalModal(self, t, await self.bot.is_premium(i)))
    
    async def interaction_check(self, i):
        if not await super().interaction_check(i): return False
        cid = i.data.get('custom_id')
        vals = i.data.get('values', [])
        
        if cid in ["color", "purgeday"] and vals:
            if not await self.bot.is_premium(i):
                class UpgradeView(MaintenanceView):
                    def __init__(self):
                        super().__init__(timeout=None)
                        self.add_item(discord.ui.Button(sku_id=config.PREMIUM_SKU_ID))
                await i.response.send_message("⭐ **Fonctionnalité Premium**\nCette option est exclusive à l'abonnement Chronis Premium. Utilisez `/premium` pour la débloquer !", view=UpgradeView(), ephemeral=True)
                return False
            
            if cid == "color": self.sel_color = vals[0]
            if cid == "purgeday": self.sel_purge_day = vals[0]
            
        elif cid == "svc" and vals: self.sel_service = vals[0]
        elif cid == "log" and vals: self.sel_logs = vals[0]
        elif cid == "role": self.sel_role = [int(v) for v in vals]
        elif cid == "autorole": self.sel_autorole = [int(v) for v in vals]
        elif cid == "citizen" and vals: self.sel_citizen = vals[0]
        elif cid == "servicerole" and vals: self.sel_service_role = vals[0]
        
        if cid in ["svc", "log", "role", "autorole", "citizen", "servicerole", "color", "purgeday"]: 
            await i.response.defer()
            await self.refresh(i)
            return False 
        return True

class RdvTypeModal(MaintenanceModal):
    def __init__(self, parent_view):
        txt = config.TRANSLATIONS[parent_view.lang]
        super().__init__(title=txt.get('rdv_modal_type_title', "Nouveau Motif"))
        self.parent = parent_view
        self.name = discord.ui.TextInput(label=txt.get('rdv_modal_type_label', "Nom"), max_length=30)
        self.add_item(self.name)
    
    async def on_submit(self, interaction: discord.Interaction):
        is_premium = await interaction.client.is_premium(interaction)
        
        if not is_premium and len(self.parent.types) >= config.FREE_RDV_LIMIT:
            embed = discord.Embed(
                title="⭐ Fonctionnalité Premium",
                description=(
                    f"La version gratuite est limitée à **{config.FREE_RDV_LIMIT} motifs de rendez-vous**.\n\n"
                    "Passez à **Chronis Premium** pour débloquer un nombre de motifs illimité et bien d'autres fonctionnalités !"
                ),
                color=0xFFD700
            )
            
            class UpgradeView(MaintenanceView):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(sku_id=config.PREMIUM_SKU_ID))
                    
            return await interaction.response.send_message(embed=embed, view=UpgradeView(), ephemeral=True)

        if self.name.value not in self.parent.types:
            self.parent.types.append(self.name.value)
            self.parent.update_components()
            await self.parent.update_embed(interaction) 
        else:
            await interaction.response.send_message("❌ Ce motif existe déjà.", ephemeral=True)

class RdvBookingModal(MaintenanceModal):
    def __init__(self, bot, rdv_type, lang):
        txt = config.TRANSLATIONS[lang]
        super().__init__(title=txt.get('rdv_modal_book_title', "RDV"))
        self.bot = bot
        self.rdv_type = rdv_type
        self.lang = lang
        self.info = discord.ui.TextInput(label=txt.get('rdv_modal_book_label', "Infos"), style=discord.TextStyle.paragraph)
        self.add_item(self.info)

    async def on_submit(self, interaction: discord.Interaction):
        txt = config.TRANSLATIONS[self.lang]
        conf = await self.bot.db.get_rdv_config(interaction.guild.id)
        if not conf or not conf['staff']: return await interaction.response.send_message(txt.get('rdv_err_config', "Erreur config."), ephemeral=True)
        channel = interaction.guild.get_channel(int(conf['staff']))
        if not channel: return await interaction.response.send_message(txt.get('rdv_err_config', "Erreur salon."), ephemeral=True)

        embed = discord.Embed(title=txt.get('rdv_new_req_title', "Nouvelle Demande"), color=discord.Color.blue())
        embed.description = f"**Patient**: {interaction.user.mention}\n**Type**: {self.rdv_type}\n**Info**: {self.info.value}"
        embed.set_footer(text=f"ID: {interaction.user.id}")
        
        view = RdvStaffView(self.bot, interaction.user.id, self.rdv_type, self.info.value, self.lang)
        content_role = f"<@&{conf['role']}>" if conf['role'] else ""
        await channel.send(content=content_role, embed=embed, view=view)
        await interaction.response.send_message("✅ Demande envoyée !", ephemeral=True)

class RdvCloseModal(MaintenanceModal):
    def __init__(self, bot, interaction):
        self.bot = bot
        self.prev_interaction = interaction
        
        conf = bot.db._config_cache.get(str(interaction.guild.id)) 
        if conf and 'data' in conf: lang = conf['data'].get('language', 'fr')
        else: lang = 'fr'
        txt = config.TRANSLATIONS[lang]
        
        super().__init__(title=txt.get('rdv_modal_close_title', "Fermeture du Dossier"))
        self.reason = discord.ui.TextInput(label=txt.get('rdv_modal_close_label', "Raison / Conclusion"), style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)
        self.lang = lang

    async def on_submit(self, interaction: discord.Interaction):
        txt = config.TRANSLATIONS[self.lang]
        await interaction.response.send_message("Génération du transcript et fermeture...", ephemeral=True)
        
        topic = interaction.channel.topic or ""
        patient_id = None
        staff_id = None
        request_ts = None
        staff_msg_id = None
        
        if "Patient:" in topic:
            try:
                parts = topic.split("|")
                for p in parts:
                    if "Patient:" in p: patient_id = int(p.split(":")[1].strip())
                    if "Staff:" in p: staff_id = int(p.split(":")[1].strip())
                    if "Date:" in p: request_ts = int(p.split(":")[1].strip())
                    if "Msg:" in p: staff_msg_id = int(p.split(":")[1].strip())
            except Exception as e: print(f"[ERREUR] Topic split: {e}")

        transcript_file = await generate_transcript_file(interaction.channel, interaction.user, self.reason.value)
        
        if patient_id:
            try:
                patient = await self.bot.fetch_user(patient_id)
                embed_dm_close = discord.Embed(title=txt['dm_close_title'], color=discord.Color.red())
                embed_dm_close.add_field(name=txt['dm_close_guild'], value=interaction.channel.name, inline=False)
                embed_dm_close.add_field(name=txt['dm_close_date'], value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=False)
                embed_dm_close.add_field(name=txt['dm_close_staff'], value=f"{interaction.user.display_name} ({interaction.user.id})", inline=False)
                embed_dm_close.add_field(name=txt['dm_close_reason'], value=self.reason.value, inline=False)
                embed_dm_close.set_footer(text=config.EMBED_FOOTER)
                
                transcript_file.fp.seek(0)
                await patient.send(embed=embed_dm_close, file=transcript_file)
                transcript_file.fp.seek(0) 
            except discord.NotFound: pass
            except Exception as e: print(f"[ERREUR] Envoi transcript DM: {e}")
            
        conf = await self.bot.db.get_rdv_config(interaction.guild.id)
        
        if staff_msg_id and conf.get('staff'):
            try:
                chan_staff = interaction.guild.get_channel(int(conf['staff']))
                if chan_staff:
                    msg = await chan_staff.fetch_message(staff_msg_id)
                    new_embed = msg.embeds[0]
                    new_embed.color = discord.Color.greyple()
                    new_embed.set_footer(text=f"Terminé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
                    await msg.edit(content=f"✅ **Rendez-vous Effectué** (Traité par {interaction.user.mention})", embed=new_embed, view=None)
            except Exception as e: print(f"[ERREUR] Update msg staff: {e}")

        if conf and conf.get('transcript'):
            try:
                log_chan = interaction.guild.get_channel(int(conf['transcript']))
                if log_chan:
                    embed_log = discord.Embed(title=txt.get('rdv_log_closed_title', "RDV Fermé"), color=discord.Color.red())
                    pat_men = f"<@{patient_id}>" if patient_id else "Inconnu"
                    stf_men = f"<@{staff_id}>" if staff_id else "Inconnu"
                    
                    embed_log.description = txt.get('rdv_log_closed_desc', "Fermé").format(patient=pat_men)
                    embed_log.add_field(name="Ouvert par (Staff)", value=stf_men, inline=True)
                    embed_log.add_field(name="Fermé par", value=interaction.user.mention, inline=True)
                    
                    if request_ts:
                        embed_log.add_field(name="📅 Créé le", value=f"<t:{request_ts}:f>", inline=False)
                    
                    embed_log.add_field(name="📝 Raison / Conclusion", value=self.reason.value, inline=False)
                    
                    embed_log.timestamp = datetime.now()
                    transcript_file.fp.seek(0)
                    await log_chan.send(embed=embed_log, file=transcript_file)
            except Exception as e: print(f"[ERREUR] Log error: {e}")

        import asyncio
        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"[ERREUR] Channel delete: {e}")

class AbsenceView(MaintenanceView):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        btn = discord.ui.Button(label=txt.get('abs_btn_end', "Fin"), style=discord.ButtonStyle.success, custom_id="absence_end_btn")
        btn.callback = self.end_absence
        self.add_item(btn)

    async def end_absence(self, interaction: discord.Interaction):
        conf_guild = await self.bot.db.get_guild_config(str(interaction.guild_id))
        lang = conf_guild.get('language', 'fr') if conf_guild else 'fr'
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        msg_id = str(interaction.message.id)
        
        absence_data = await self.bot.db.get_absence_by_message_id(msg_id)
        
        if not absence_data:
            return await interaction.response.send_message("❌ Cette absence n'existe plus dans la base de données.", ephemeral=True)

        owner_id = absence_data['user_id']

        if str(interaction.user.id) != str(owner_id) and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(txt.get('abs_err_owner', "Pas toi !"), ephemeral=True)
            
        await self.bot.db.end_absence(msg_id)
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=txt.get('abs_ended', "Terminée"))
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(txt.get('abs_ended', "Terminée"), ephemeral=True)

class RdvSetupView(MaintenanceView):
    def __init__(self, bot, config_data):
        super().__init__(timeout=300)
        self.bot = bot
        self.config = config_data or {}
        self.lang = 'fr'
        self.public_id = self.config.get('public')
        self.staff_id = self.config.get('staff')
        self.transcript_id = self.config.get('transcript')
        self.role_id = self.config.get('role')
        self.types = self.config.get('types', [])
        self.update_components()

    def update_components(self):
        self.clear_items()
        txt = config.TRANSLATIONS[self.lang]
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_public', "Salon Public"), custom_id="rdv_pub", channel_types=[discord.ChannelType.text]))
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_staff', "Salon Staff"), custom_id="rdv_stf", channel_types=[discord.ChannelType.text]))
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_transcript', "Salon Logs/Transcript"), custom_id="rdv_trs", channel_types=[discord.ChannelType.text])) 
        self.add_item(discord.ui.RoleSelect(placeholder=txt.get('rdv_ph_role', "Rôle Staff"), custom_id="rdv_rol"))
        
        btn_add = discord.ui.Button(label=txt.get('rdv_btn_add', "Ajouter Motif"), style=discord.ButtonStyle.success, custom_id="rdv_add", row=4)
        btn_add.callback = self.add_type
        self.add_item(btn_add)
        
        if self.types:
            btn_del = discord.ui.Button(label=txt.get('rdv_btn_del', "Supprimer Motif"), style=discord.ButtonStyle.danger, custom_id="rdv_del", row=4)
            btn_del.callback = self.remove_type_menu
            self.add_item(btn_del)
            
        btn_save = discord.ui.Button(label=txt.get('setup_btn_save', "Sauvegarder"), style=discord.ButtonStyle.primary, custom_id="rdv_save", row=4)
        btn_save.callback = self.save_config
        self.add_item(btn_save)

    async def update_embed(self, interaction):
        txt = config.TRANSLATIONS[self.lang]
        types_list = "\n".join([f"• {t}" for t in self.types]) if self.types else "Aucun"
        embed = interaction.message.embeds[0]
        embed.description = txt['rdv_setup_desc'].format(types=types_list)
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if not await super().interaction_check(interaction): return False
        cid = interaction.data.get('custom_id')
        vals = interaction.data.get('values', [])
        if cid == "rdv_pub": self.public_id = vals[0]
        elif cid == "rdv_stf": self.staff_id = vals[0]
        elif cid == "rdv_trs": self.transcript_id = vals[0]
        elif cid == "rdv_rol": self.role_id = vals[0]
        if cid in ["rdv_pub", "rdv_stf", "rdv_trs", "rdv_rol"]: 
             await interaction.response.defer()
             return False
        return True

    async def add_type(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RdvTypeModal(self))

    async def remove_type_menu(self, interaction: discord.Interaction):
        view = RdvDeleteTypeView(self)
        await interaction.response.send_message("Supprimer quel motif ?", view=view, ephemeral=True)

    async def save_config(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        txt = config.TRANSLATIONS[self.lang]
        msg_id = None
        if self.public_id and self.types:
            try:
                public_channel = interaction.guild.get_channel(int(self.public_id))
                if public_channel:
                    embed_panel = discord.Embed(title=txt['rdv_panel_title'], description=txt['rdv_panel_desc'], color=discord.Color.blue())
                    view_panel = RdvPatientView(self.bot, self.types, self.lang)
                    old_msg_id = self.config.get('message_id')
                    message_sent = False
                    if old_msg_id:
                        try:
                            msg = await public_channel.fetch_message(int(old_msg_id))
                            await msg.edit(embed=embed_panel, view=view_panel)
                            msg_id = str(msg.id)
                            message_sent = True
                        except discord.NotFound: pass
                        except Exception as e: print(f"[ERREUR] fetch msg RDV: {e}")
                    if not message_sent:
                        msg = await public_channel.send(embed=embed_panel, view=view_panel)
                        msg_id = str(msg.id)
            except Exception as e: print(f"[ERREUR] panel auto RDV: {e}")

        await self.bot.db.set_rdv_config(interaction.guild.id, self.public_id, self.staff_id, self.transcript_id, self.role_id, self.types, msg_id)
        await interaction.followup.send("✅ Configuration RDV sauvegardée et Panneau mis à jour !", ephemeral=True)

class RdvDeleteTypeView(MaintenanceView):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent = parent_view
        select = discord.ui.Select(placeholder="Choisir...", min_values=1, max_values=1)
        for t in parent_view.types[:25]: select.add_option(label=t, value=t)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        val = interaction.data['values'][0]
        if val in self.parent.types:
            self.parent.types.remove(val)
            self.parent.update_components()
            await interaction.response.edit_message(content=f"🗑️ Motif `{val}` supprimé.", view=None)
            try: await self.parent.update_embed(interaction) 
            except Exception as e: print(f"[ERREUR] RdvDeleteTypeView update embed: {e}")

class RdvPatientView(MaintenanceView):
    def __init__(self, bot, types, lang):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        self.types = types 
        txt = config.TRANSLATIONS[lang]
        self.select = discord.ui.Select(placeholder=txt.get('rdv_select_ph', "Choisir..."), custom_id="rdv_patient_select", min_values=1, max_values=1)
        for t in types: self.select.add_option(label=t, value=t)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        rdv_type = self.select.values[0]
        await interaction.response.send_modal(RdvBookingModal(self.bot, rdv_type, self.lang))
        self.select.options.clear()
        for t in self.types: self.select.add_option(label=t, value=t, default=False)
        self.select.placeholder = config.TRANSLATIONS[self.lang].get('rdv_select_ph', "Choisir...")
        try: await interaction.message.edit(view=self)
        except discord.NotFound: pass
        except Exception as e: print(f"[ERREUR] RdvPatientView edit: {e}")

class RdvStaffView(MaintenanceView):
    def __init__(self, bot, user_id=None, rdv_type=None, info=None, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.rdv_type = rdv_type
        self.info = info
        self.lang = lang
        
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        b_acc = discord.ui.Button(label=txt.get('rdv_btn_accept', "Accepter"), style=discord.ButtonStyle.success, custom_id="rdv_accept")
        b_acc.callback = self.accept
        self.add_item(b_acc)
        
        b_ref = discord.ui.Button(label=txt.get('rdv_btn_refuse', "Refuser"), style=discord.ButtonStyle.danger, custom_id="rdv_refuse")
        b_ref.callback = self.refuse
        self.add_item(b_ref)

    async def _get_data(self, interaction):
        if self.user_id and self.rdv_type:
            return self.user_id, self.rdv_type, self.info, self.lang

        try:
            conf_guild = await self.bot.db.get_guild_config(str(interaction.guild_id))
            lang = conf_guild.get('language', 'fr') if conf_guild else 'fr'

            embed = interaction.message.embeds[0]
            
            footer_text = embed.footer.text
            user_id = int(footer_text.replace("ID:", "").strip())
            
            desc = embed.description
            rdv_type = "Inconnu"
            info = "Non spécifié"
            
            for line in desc.split('\n'):
                if "**Type**" in line:
                    rdv_type = line.split(":", 1)[1].strip()
                if "**Info**" in line:
                    info = line.split(":", 1)[1].strip()
                    
            return user_id, rdv_type, info, lang
        except Exception as e:
            print(f"[ERREUR] récupération données RDV : {e}")
            return None, None, None, 'fr'

    async def accept(self, interaction: discord.Interaction):
        user_id, rdv_type, info, lang = await self._get_data(interaction)
        
        if not user_id:
            return await interaction.response.send_message("❌ Erreur : Impossible de retrouver le dossier (Données illisibles).", ephemeral=True)

        txt = config.TRANSLATIONS[lang]
        guild = interaction.guild
        try: 
            user = guild.get_member(user_id) or await guild.fetch_member(user_id)
        except discord.NotFound: 
            return await interaction.response.send_message("⚠️ Utilisateur introuvable (a peut-être quitté le serveur).", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR] accept rdv fetch_member: {e}")
            return await interaction.response.send_message("❌ Erreur.", ephemeral=True)
        
        request_time = interaction.message.created_at
        request_ts = int(request_time.timestamp())
        
        staff_msg_id = interaction.message.id

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        
        conf = await self.bot.db.get_rdv_config(guild.id)
        role_mention = ""
        if conf and conf['role']:
            role = guild.get_role(int(conf['role']))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)
                role_mention = role.mention

        cat = discord.utils.get(guild.categories, name="Rendez-Vous")
        if not cat: cat = await guild.create_category("Rendez-Vous")
        
        chan_name = f"rdv-{user.name}-{rdv_type}"
        chan_name = chan_name.replace(" ", "-").lower()[:99]
        
        topic_info = f"Patient: {user.id} | Staff: {interaction.user.id} | Type: {rdv_type} | Date: {request_ts} | Msg: {staff_msg_id}"
        
        channel = await guild.create_text_channel(chan_name, category=cat, overwrites=overwrites, topic=topic_info)
        
        welcome_msg = txt.get('rdv_ticket_welcome', "Bienvenue").format(user=user.mention, role=role_mention, type=rdv_type, info=info)
        await channel.send(welcome_msg, view=RdvTicketView(self.bot, lang))
        
        await interaction.message.edit(view=None, content=txt.get('rdv_accepted', "Accepté").format(staff=interaction.user.mention, channel=channel.mention), embed=interaction.message.embeds[0])

        try:
            embed_dm_acc = discord.Embed(title="✅ Demande de RDV Acceptée", color=discord.Color.green())
            embed_dm_acc.description = f"Votre demande a été acceptée par {interaction.user.mention}.\n\n🔗 **Accéder au salon :** [Cliquez ici]({channel.jump_url})"
            embed_dm_acc.set_footer(text=config.EMBED_FOOTER)
            await user.send(embed=embed_dm_acc)
        except discord.Forbidden: pass
        except Exception as e: print(f"[ERREUR] send dm rdv: {e}")

        if conf.get('transcript'):
            try:
                log_chan = guild.get_channel(int(conf['transcript']))
                if log_chan:
                    embed_log = discord.Embed(title=txt.get('rdv_log_accepted_title', "RDV Accepté"), color=discord.Color.green())
                    embed_log.description = txt.get('rdv_log_accepted_desc', "Accepté par {staff}").format(staff=interaction.user.mention, patient=user.mention)
                    embed_log.add_field(name="Type", value=rdv_type, inline=True)
                    embed_log.add_field(name="📅 Demandé le", value=f"<t:{request_ts}:f>", inline=True)
                    embed_log.timestamp = datetime.now()
                    await log_chan.send(embed=embed_log)
            except Exception as e: print(f"[ERREUR] log rdv: {e}")

    async def refuse(self, interaction: discord.Interaction):
        _, _, _, lang = await self._get_data(interaction)
        txt = config.TRANSLATIONS[lang]
        await interaction.message.edit(view=None, content=txt.get('rdv_refused', "Refusé par {user}.").format(user=interaction.user.mention), embed=interaction.message.embeds[0])

class RdvTicketView(MaintenanceView):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        btn = discord.ui.Button(label=txt.get('rdv_btn_close', "Fermer"), style=discord.ButtonStyle.danger, emoji="🔒", custom_id="rdv_ticket_close")
        btn.callback = self.close
        self.add_item(btn)

    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RdvCloseModal(self.bot, interaction))

class ServerStatsView(MaintenanceView):
    def __init__(self, bot, guild_id, sessions, stats, lang, bot_color):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.sessions = sessions
        self.stats = stats
        self.lang = lang
        self.bot_color = bot_color
        self.mode = 'weekly'
        self.graph_index = 0
        self.graphs_weekly = ['weekly_hours', 'weekly_staff', 'weekly_avg']
        self.graphs_daily = ['daily_activity', 'daily_sessions']
        
        self.last_7_days_dates = [datetime.now().date() - timedelta(days=i) for i in range(7)]
        self.update_components()

    def update_components(self):
        self.clear_items()
        txt = config.TRANSLATIONS[self.lang]
        
        select_mode = discord.ui.Select(placeholder=txt['srv_select_placeholder'], min_values=1, max_values=1, custom_id="stats_mode", row=0)
        select_mode.add_option(label=txt['srv_opt_weekly'], value='weekly', emoji="🗓️", default=(self.mode=='weekly'))
        select_mode.add_option(label=txt['srv_opt_daily'], value='daily', emoji="📅", default=(self.mode=='daily'))
        select_mode.callback = self.select_callback
        self.add_item(select_mode)
        
        days_fr = {
            'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
        }
        
        ph_text = "🔎 Détail par jour (Activité Horaire)" if self.lang == 'fr' else "🔎 Daily Detail (Hourly Activity)"
        select_day = discord.ui.Select(placeholder=ph_text, min_values=1, max_values=1, custom_id="stats_day", row=1)
        
        for d in self.last_7_days_dates:
            day_name_en = d.strftime("%A")
            day_name = days_fr.get(day_name_en, day_name_en) if self.lang == 'fr' else day_name_en
            
            label = f"{day_name} {d.strftime('%d/%m')}" 
            value = d.strftime("%Y-%m-%d")
            select_day.add_option(label=label, value=value, emoji="📊")
            
        select_day.callback = self.day_callback
        self.add_item(select_day)

        btn = discord.ui.Button(label=txt['srv_btn_next_graph'], style=discord.ButtonStyle.primary, custom_id="next_graph", row=2)
        btn.callback = self.button_callback
        self.add_item(btn)

    async def select_callback(self, interaction: discord.Interaction):
        self.mode = interaction.data['values'][0]
        self.graph_index = 0
        self.update_components()
        await interaction.response.defer()
        await self.update_message(interaction)

    async def day_callback(self, interaction: discord.Interaction):
        date_str = interaction.data['values'][0]
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        await interaction.response.defer()
        
        day_sessions = await self.bot.db.get_sessions_on_date(self.guild_id, target_date)
        file = await create_graph(day_sessions, "hourly_specific_day", self.lang, target_date=target_date)
        embed = create_server_stats_embed(self.stats, self.stats['days_analyzed'], self.lang, self.bot_color)
        
        try: await interaction.edit_original_response(embed=embed, attachments=[file] if file else [], view=self)
        except Exception as e: 
            print(f"[ERREUR] edit graph: {e}")
            await interaction.response.edit_message(embed=embed, attachments=[file] if file else [], view=self)

    async def button_callback(self, interaction: discord.Interaction):
        current_list = self.graphs_weekly if self.mode == 'weekly' else self.graphs_daily
        self.graph_index = (self.graph_index + 1) % len(current_list)
        await interaction.response.defer()
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        current_list = self.graphs_weekly if self.mode == 'weekly' else self.graphs_daily
        graph_type = current_list[self.graph_index]
        file = await create_graph(self.sessions, graph_type, self.lang)
        embed = create_server_stats_embed(self.stats, self.stats['days_analyzed'], self.lang, self.bot_color)
        try: await interaction.edit_original_response(embed=embed, attachments=[file] if file else [], view=self)
        except Exception as e: 
            print(f"[ERREUR] update_message graph: {e}")
            await interaction.response.edit_message(embed=embed, attachments=[file] if file else [], view=self)

class PaginationView(MaintenanceView):
    def __init__(self, bot, all_stats, guild, lang, goal=0, absent_users=None, bot_color=config.BOT_COLOR):
        super().__init__(timeout=300)
        self.bot = bot
        self.all_stats = all_stats
        self.guild = guild
        self.lang = lang
        self.goal = goal
        self.absent_users = absent_users if absent_users else []
        self.current_page = 1
        self.txt = config.TRANSLATIONS[lang]
        self.message = None
        self.bot_color = bot_color
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']
        import math
        total_pages = math.ceil(len(self.all_stats) / 10) or 1
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_embed(interaction)

    @discord.ui.button(label="📁 Exporter (CSV)", style=discord.ButtonStyle.success, custom_id="export_csv_btn", row=0)
    async def export_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_premium = await interaction.client.is_premium(interaction)
        
        if not is_premium:
            from utils import has_voted_topgg
            has_voted = await has_voted_topgg(str(interaction.user.id))
            
            if not has_voted:
                embed = discord.Embed(
                    title="⭐ Exportation : Premium ou Vote",
                    description=(
                        "L'exportation Excel est une fonctionnalité Avancée.\n\n"
                        "Pour l'utiliser **gratuitement**, soutenez-nous en votant pour le bot sur Top.gg ! "
                        "Cela débloquera l'exportation pour vous pendant 12 heures.\n\n"
                        "*(Ou passez à Chronis Premium pour débloquer cette limite à vie !)*"
                    ),
                    color=0xFFD700
                )
                class UnlockView(MaintenanceView):
                    def __init__(self):
                        super().__init__(timeout=None)
                        self.add_item(discord.ui.Button(label="Voter & Débloquer", url=config.VOTE_LINK, emoji="🗳️"))
                        self.add_item(discord.ui.Button(label="Passer Premium", sku_id=config.PREMIUM_SKU_ID))
                return await interaction.response.send_message(embed=embed, view=UnlockView(), ephemeral=True)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', dialect='excel') 
        writer.writerow(['ID Utilisateur', 'Nom / Pseudo', 'Total Sessions', 'Temps Total (Formaté)'])

        for s in self.all_stats:
            formatted_time = format_duration(s['total_time'] or 0)
            writer.writerow([s['user_id'], s['username'], s['total_sessions'], formatted_time])

        output.seek(0)
        file_data = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        date_str = datetime.now().strftime("%Y-%m-%d")
        discord_file = discord.File(fp=file_data, filename=f"Export_Chronis_{date_str}.csv")

        await interaction.response.send_message(
            content="✅ **Exportation réussie !** Voici les données actuelles du classement :", 
            file=discord_file, 
            ephemeral=True
        )

    async def update_embed(self, interaction):
        embed, total = create_all_stats_embed(self.all_stats, self.guild, self.lang, self.current_page, self.goal, self.absent_users, self.bot_color)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
        self.message = interaction.message

    async def on_timeout(self):
        for child in self.children: child.disabled = True
        if self.message:
            try: await self.message.edit(view=self)
            except discord.NotFound: pass
            except Exception as e: print(f"[ERREUR] timeout PaginationView: {e}")

class HistoryPaginationView(MaintenanceView):
    def __init__(self, sessions, user, first, last, lang, bot_color):
        super().__init__(timeout=300)
        self.sessions = sessions
        self.user = user
        self.first = first
        self.last = last
        self.lang = lang
        self.current_page = 1
        self.items_per_page = 10
        self.txt = config.TRANSLATIONS[lang]
        self.bot_color = bot_color
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']
        import math
        total_pages = math.ceil(len(self.sessions) / self.items_per_page)
        total_pages = 1 if total_pages == 0 else total_pages
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)

    def get_embed(self):
        txt = self.txt
        import math
        total_pages = math.ceil(len(self.sessions) / self.items_per_page) or 1
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        current = self.sessions[start:end]
        
        embed = discord.Embed(title=txt['det_title'].format(user=self.user.display_name), color=self.bot_color)
        f_str = f"<t:{int(self.first/1000)}:D>" if self.first else "N/A"
        l_str = f"<t:{int(self.last/1000)}:D>" if self.last else "N/A"
        embed.description = txt.get('det_range', "").format(first=f_str, last=l_str)
        
        hist_text = ""
        for s in current:
            date = f"<t:{int(s['start_time']/1000)}:f>"
            dur = format_duration(s['total_duration'])
            if s['start_time'] == s['end_time']:
                icon = "🔧"
                t = txt['det_type_adjust']
                dur = f"+{dur}" if s['total_duration'] > 0 else dur
            else:
                icon = "🟢"
                t = txt['det_type_service']
                if s.get('end_time'):
                    date += f" → <t:{int(s['end_time']/1000)}:t>"
            hist_text += f"{icon} **{date}** • {t} : `{dur}`\n"
            
        embed.add_field(name=txt['det_history'].format(count=len(self.sessions)), value=hist_text or "Vide", inline=False)
        embed.set_footer(text=f"Page {self.current_page}/{total_pages} | {config.EMBED_FOOTER}")
        return embed

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class ServiceButtonsView(MaintenanceView):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db
        texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        for c in self.children:
            if isinstance(c, discord.ui.Button):
                if c.custom_id == config.BUTTONS['start']['custom_id']:
                    c.label = texts['btn_start']
                    c.emoji = config.BUTTONS['start']['emoji']
                elif c.custom_id == config.BUTTONS['pause']['custom_id']:
                    c.label = texts['btn_pause']
                    c.emoji = config.BUTTONS['pause']['emoji']
                elif c.custom_id == config.BUTTONS['stop']['custom_id']:
                    c.label = texts['btn_stop']
                    c.emoji = config.BUTTONS['stop']['emoji']

    async def _handle_service_role(self, interaction: discord.Interaction, config_data: dict, give_role: bool):
        if not config_data:
            return
            
        role_id = config_data.get('service_role_id')
        if not role_id or role_id == "None":
            return 
            
        is_premium = await interaction.client.is_premium(interaction)
        if not is_premium:
            return 
            
        role = interaction.guild.get_role(int(role_id))
        if not role:
            return
            
        try:
            if give_role and role not in interaction.user.roles:
                await interaction.user.add_roles(role)
            elif not give_role and role in interaction.user.roles:
                await interaction.user.remove_roles(role)
        except discord.Forbidden:
            pass 
        except Exception as e:
            print(f"[ERREUR] _handle_service_role: {e}")

    async def _check_access(self, interaction):
        cd = await self.db.get_guild_config(str(interaction.guild_id)) 
        if cd is None: cd = {}
        lang = cd.get('language', 'fr')
        
        if self.bot.maintenance_mode:
            if str(interaction.user.id) == str(config.OWNER_ID):
                return True
            await interaction.followup.send(config.TRANSLATIONS[lang]['maint_block_msg'], ephemeral=True)
            return False

        allowed = json.loads(cd.get('allowed_roles', '[]') or '[]')
        if not check_permissions(interaction.user, allowed): 
            await interaction.followup.send(config.TRANSLATIONS[lang]['error_perms'], ephemeral=True)
            return False
            
        return True

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_access(interaction): return
        
        lang = await self.bot.db.get_guild_config(str(interaction.guild_id))
        if lang is None: lang = {}
        texts = config.TRANSLATIONS[lang.get('language', 'fr')]
        
        try:
            if await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)): 
                return await interaction.followup.send(texts['service_already_started'], ephemeral=True)
            
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await self._handle_service_role(interaction, lang, give_role=True)
            await interaction.followup.send(texts['service_started'], ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_start_title'], texts['log_start_desc'].format(user=interaction.user.mention), config.COLOR_GREEN)
            await self.bot.update_service_message(interaction.guild_id, None, None)
        except Exception as e: 
            print(f"[ERREUR] start_button: {e}")
            await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_access(interaction): return
        
        cd = await self.db.get_guild_config(str(interaction.guild_id)) 
        lang = cd.get('language', 'fr') if cd else 'fr'
        txt = config.TRANSLATIONS[lang]

        try:
            act = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not act: 
                return await interaction.followup.send(txt['service_not_started'], ephemeral=True)
            
            if act['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                await self._handle_service_role(interaction, cd, give_role=True)
                
                embed = discord.Embed(title="▶️ Service Repris", color=discord.Color.green())
                embed.description = f"Bon retour au travail {interaction.user.mention} !"
                now = int(datetime.now().timestamp() * 1000)
                pause_len = now - act['pause_start']
                embed.add_field(name="Durée de la pause", value=f"`{format_duration(pause_len)}`", inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                await self.bot.send_log(interaction.guild.id, txt['log_resume_title'], txt['log_resume_desc'].format(user=interaction.user.mention), config.COLOR_BLUE)
            
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                await self._handle_service_role(interaction, cd, give_role=False)
                
                embed = discord.Embed(title="⏸️ Service en Pause", color=discord.Color.orange())
                embed.description = f"Reposez-vous bien {interaction.user.mention}."
                embed.add_field(name="Heure de départ", value=f"<t:{int(datetime.now().timestamp())}:T>", inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                await self.bot.send_log(interaction.guild.id, txt['log_pause_title'], txt['log_pause_desc'].format(user=interaction.user.mention), config.COLOR_ORANGE)
            
            await self.bot.update_service_message(interaction.guild_id, None, None)
        except Exception as e: 
            print(f"[ERREUR] pause_button: {e}")
            await interaction.followup.send(txt['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_access(interaction): return
        
        cd = await self.db.get_guild_config(str(interaction.guild_id)) 
        lang = cd.get('language', 'fr') if cd else 'fr'
        txt = config.TRANSLATIONS[lang]
        
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)): 
                return await interaction.followup.send(txt['service_not_started'], ephemeral=True)
            
            end = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if end:
                await self._handle_service_role(interaction, cd, give_role=False)
                tot = end['total_duration'] + end['pause_duration']
                start_ts = int(end['start_time'] / 1000)
                end_ts = int(end['end_time'] / 1000)
                
                embed = discord.Embed(title="🛑 Fin de Service", color=discord.Color.red())
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                
                embed.add_field(name="🕒 Horaires", value=f"Début : <t:{start_ts}:T>\nFin : <t:{end_ts}:T>", inline=True)
                embed.add_field(name="⏱️ Chrono", value=f"Total : `{format_duration(tot)}`\nPause : `{format_duration(end['pause_duration'])}`", inline=True)
                embed.add_field(name="✅ Temps Effectif (Comptabilisé)", value=f"`{format_duration(end['total_duration'])}`", inline=False)
                
                embed.set_footer(text="Merci pour votre travail ! | Session enregistrée")

                await interaction.followup.send(embed=embed, ephemeral=True)
                
                await self.bot.send_log(interaction.guild.id, txt['log_stop_title'], txt['log_stop_desc'].format(user=interaction.user.mention), config.COLOR_RED, [("Total", format_duration(tot))])
                await self.bot.update_service_message(interaction.guild_id, None, None)
            else: 
                await interaction.followup.send(txt['error_db'], ephemeral=True)
        except Exception as e: 
            print(f"[ERREUR] stop_button: {e}")
            await interaction.followup.send(txt['error_db'], ephemeral=True)

class EditTimeView(MaintenanceView):
    def __init__(self, bot, lang, target, bot_color=config.BOT_COLOR):
        super().__init__(timeout=60)
        self.bot = bot
        self.lang = lang
        self.target = target
        self.bot_color = bot_color
        t = config.TRANSLATIONS[lang]
        self.add_item(discord.ui.Button(label=t['et_btn_add'], emoji="➕", custom_id="add", style=discord.ButtonStyle.success))
        self.add_item(discord.ui.Button(label=t['et_btn_remove'], emoji="➖", custom_id="remove", style=discord.ButtonStyle.danger))
    
    async def interaction_check(self, i):
        if not await super().interaction_check(i): return False
        await i.response.send_modal(EditTimeModal(self.bot, self.lang, self.target, i.data['custom_id'], self.bot_color))
        return False

class FeedbackTypeSelect(discord.ui.Select):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        t = config.TRANSLATIONS[lang]
        ops = [discord.SelectOption(label=t['fb_opt_review'], value="review", emoji="⭐"), discord.SelectOption(label=t['fb_opt_bug'], value="bug", emoji="🐛")]
        super().__init__(placeholder=t['fb_select_placeholder'], options=ops)
        
    async def callback(self, i): 
        if self.values[0] == "review": await i.response.send_modal(ReviewModal(self.bot, self.lang))
        elif self.values[0] == "bug": await i.response.send_modal(BugReportModal(self.bot, self.lang))

class FeedbackView(MaintenanceView):
    def __init__(self, bot, lang): 
        super().__init__(timeout=60)
        self.add_item(FeedbackTypeSelect(bot, lang))

class AboutView(MaintenanceView):
    def __init__(self, bot, lang, bot_color=config.BOT_COLOR, show_partner=False):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        self.bot_color = bot_color
        self.show_partner = show_partner
        
        self.add_item(discord.ui.Button(label="➕ Inviter le bot", style=discord.ButtonStyle.link, url=config.INVITE_LINK))
        if show_partner:
            self.add_item(discord.ui.Button(label="Hébergement Hosterfy (-5%)", style=discord.ButtonStyle.link, url=config.AFFILIATE_LINK, emoji="🌐"))
        self.add_item(discord.ui.Button(label="Voter" if lang == 'fr' else "Vote", style=discord.ButtonStyle.link, url=config.VOTE_LINK, emoji="🗳️"))
        
    def get_embed(self):
        txt = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        ping = round(self.bot.latency * 1000)
        guilds = len(self.bot.guilds)
        python_v = sys.version.split()[0]
        discord_v = discord.__version__
        bot_version = getattr(config, 'BOT_VERSION', 'Inconnue')
        
        if self.lang == 'en':
            def_title = "ℹ️ System Info"
            def_desc = "Service management bot, time tracking and statistics."
            lbl_ping = "🏓 Latency"
            lbl_guilds = "🌍 Servers"
            lbl_version = "⚙️ Version"
        else:
            def_title = "ℹ️ Informations Système"
            def_desc = "Bot de gestion de service, pointage et statistiques."
            lbl_ping = "🏓 Latence"
            lbl_guilds = "🌍 Serveurs"
            lbl_version = "⚙️ Version"

        title = txt.get('about_title', def_title)
        desc = txt.get('about_description', def_desc)

        embed = discord.Embed(title=title, description=desc, color=self.bot_color)
        embed.add_field(name=txt.get('about_field_latency', lbl_ping), value=f"`{ping}ms`", inline=True)
        embed.add_field(name=txt.get('about_field_servers', lbl_guilds), value=f"`{guilds}`", inline=True)
        embed.add_field(name=txt.get('about_field_version', lbl_version), value=f"`{bot_version}`", inline=True)
        embed.add_field(name="🐍 Python", value=f"`{python_v}`", inline=True)
        embed.add_field(name="📚 Discord.py", value=f"`{discord_v}`", inline=True)
        if self.show_partner:
            hosterfy_offer = ("Host your server with 5% off using code **CHRONISBOT**."
                              if self.lang == 'en' else
                              "Hébergez votre serveur avec 5 % de réduction grâce au code **CHRONISBOT**.")
            embed.add_field(name="🌐 Hosterfy", value=hosterfy_offer, inline=False)
        
        embed.set_footer(text=config.EMBED_FOOTER)
        return embed

class HelpView(MaintenanceView):
    def __init__(self, bot, bot_color=config.BOT_COLOR, show_partner=False):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = 'fr' 
        self.bot_color = bot_color
        self.show_partner = show_partner
        
    def get_embed(self, cat=None):
        t = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        root_description = f"{t['help_desc']}\n\n{t['help_contact_dm']}"
        if cat == 'root':
            return discord.Embed(title=t['help_title'], description=root_description, color=self.bot_color)
        
        if cat == 'user': 
            embed = discord.Embed(title=f"{t['help_title']} - {t['help_cat_user']}", description=t['help_user_desc'], color=self.bot_color)
            embed.add_field(name="Liste", value=t['help_cmds_user'], inline=False)
            return embed
            
        elif cat == 'admin': 
            embed = discord.Embed(title=f"{t['help_title']} - {t['help_cat_admin']}", description=t['help_admin_desc'], color=self.bot_color)
            if 'help_cmds_admin_1' in t:
                embed.add_field(name="Gestion (1/2)", value=t['help_cmds_admin_1'], inline=False)
                embed.add_field(name="Gestion (2/2)", value=t['help_cmds_admin_2'], inline=False)
            else:
                embed.add_field(name="Liste", value=t['help_cmds_admin'], inline=False)
            return embed

        elif cat == 'premium':
            embed = discord.Embed(title=f"{t['help_title']} - {t['help_cat_premium']} 💎", description=t['help_premium_desc'], color=0xFFD700)
            embed.add_field(name="Liste", value=t['help_cmds_premium'], inline=False)
            return embed
            
        return discord.Embed(title=t['help_title'], description=root_description, color=self.bot_color)
        
    def update_buttons(self, state):
        self.clear_items()
        t = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        if state == 'lang':
            self.add_item(discord.ui.Button(label="Français", emoji="🇫🇷", custom_id="fr", style=discord.ButtonStyle.primary))
            self.children[0].callback = self.cb_fr
            self.add_item(discord.ui.Button(label="English", emoji="🇬🇧", custom_id="en", style=discord.ButtonStyle.primary))
            self.children[1].callback = self.cb_en
        elif state == 'menu':
            self.add_item(discord.ui.Button(label=t['help_cat_user'], style=discord.ButtonStyle.success, emoji="👤", row=0))
            self.children[0].callback = self.cb_user
            self.add_item(discord.ui.Button(label=t['help_cat_admin'], style=discord.ButtonStyle.danger, emoji="🛡️", row=0))
            self.children[1].callback = self.cb_admin
            self.add_item(discord.ui.Button(label=t['help_cat_premium'], style=discord.ButtonStyle.secondary, emoji="💎", row=0))
            self.children[2].callback = self.cb_premium
            
            self.add_item(discord.ui.Button(label=t['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1))
            self.children[3].callback = self.cb_feed
            self.add_item(discord.ui.Button(label=t['help_back_lang'], emoji="🌍", style=discord.ButtonStyle.secondary, row=1))
            self.children[4].callback = self.cb_back
        elif state == 'sub':
            self.add_item(discord.ui.Button(label=t['help_back'], style=discord.ButtonStyle.secondary, emoji="↩️"))
            self.children[0].callback = self.cb_menu

        if self.show_partner:
            label = ('Hosterfy -5% | code CHRONISBOT' if self.lang == 'fr'
                     else 'Hosterfy 5% off | code CHRONISBOT')
            self.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.link,
                                            url=config.AFFILIATE_LINK, emoji='🌐', row=4))

    async def refresh_partner(self, interaction):
        self.show_partner = bool(interaction.guild_id) and not await self.bot.is_premium(interaction)
            
    async def cb_fr(self, i): await self.refresh_partner(i); self.lang='fr'; self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_en(self, i): await self.refresh_partner(i); self.lang='en'; self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_back(self, i): await self.refresh_partner(i); self.update_buttons('lang'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_menu(self, i): await self.refresh_partner(i); self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_user(self, i): await self.refresh_partner(i); self.update_buttons('sub'); await i.response.edit_message(embed=self.get_embed('user'), view=self)
    async def cb_admin(self, i): await self.refresh_partner(i); self.update_buttons('sub'); await i.response.edit_message(embed=self.get_embed('admin'), view=self)
    async def cb_premium(self, i): await self.refresh_partner(i); self.update_buttons('sub'); await i.response.edit_message(embed=self.get_embed('premium'), view=self)
    async def cb_feed(self, i): await i.response.send_message(view=FeedbackView(self.bot, self.lang), ephemeral=True)
