import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from typing import List
from datetime import datetime
from utils import create_stats_embed, create_all_stats_embed, create_service_embed, format_duration
import config

# --- LOGIQUE FEEDBACK CENTRALISÉE ---
async def send_feedback_log(bot, interaction, title, color, fields):
    """Envoie le feedback dans le salon privé du développeur."""
    target_id = config.DEV_FEEDBACK_CHANNEL_ID
    channel = bot.get_channel(target_id)
    
    if channel is None:
        try: channel = await bot.fetch_channel(target_id)
        except: return False
    
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
        except: return False
    return False

# --- MODALES FEEDBACK ---
class ReviewModal(discord.ui.Modal):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_review_title'])

        self.subject = discord.ui.TextInput(label=texts['fb_review_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.rating = discord.ui.TextInput(label=texts['fb_review_rating'], style=discord.TextStyle.short, placeholder="5", required=True, max_length=1)
        self.comment = discord.ui.TextInput(label=texts['fb_review_comment'], style=discord.TextStyle.paragraph, required=True, max_length=1000)
        
        self.add_item(self.subject)
        self.add_item(self.rating)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            stars = int(self.rating.value)
            stars = max(1, min(5, stars))
            star_str = "⭐" * stars
        except: star_str = "❓"

        fields = [
            ("📌 Sujet", f"**{self.subject.value}**"),
            (texts['fb_field_rating'], f"{star_str} ({self.rating.value}/5)"),
            ("💬 Commentaire", self.comment.value)
        ]
        
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_review_title'], discord.Color.gold(), fields)
        if success: await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else: await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class BugReportModal(discord.ui.Modal):
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
        fields = [("📌 Sujet", f"**{self.subject.value}**"), ("📝 Description", self.description.value)]
        if self.media.value: fields.append((texts['fb_field_media'], self.media.value))
        
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_bug_title'], discord.Color.red(), fields)
        if success: await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else: await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class FeedbackTypeSelect(discord.ui.Select):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        options = [
            discord.SelectOption(label=texts['fb_opt_review'], value="review", description="Note & Avis", emoji="⭐"),
            discord.SelectOption(label=texts['fb_opt_bug'], value="bug", description="Bug Report", emoji="🐛")
        ]
        super().__init__(placeholder=texts['fb_select_placeholder'], min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "review": await interaction.response.send_modal(ReviewModal(self.bot, self.lang))
        elif self.values[0] == "bug": await interaction.response.send_modal(BugReportModal(self.bot, self.lang))

class FeedbackView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=60)
        self.add_item(FeedbackTypeSelect(bot, lang))

# --- MODALE ABSENCE (CORRIGÉE) ---
class AbsenceModal(discord.ui.Modal):
    def __init__(self, bot, lang, direction_role_id):
        self.bot = bot
        self.lang = lang
        self.direction_role_id = direction_role_id
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
            
            if d2 < d1: return await interaction.response.send_message(texts['abs_error_logic'], ephemeral=True)
            
            delta = d2 - d1
            days = delta.days + 1
            duration_str = f"{days} jour(s)" if self.lang == 'fr' else f"{days} day(s)"
            
            # --- MODIFICATION ICI ---
            # On utilise le display_name pour le titre (texte brut)
            try:
                title_text = texts['abs_embed_title'].format(user=interaction.user.display_name)
            except KeyError:
                title_text = f"Absence : {interaction.user.display_name}"

            embed = discord.Embed(title=title_text, color=discord.Color.purple(), timestamp=datetime.now())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # On ajoute un champ "Agent" qui contient la VRAIE mention cliquable
            embed.add_field(name="👤 Agent", value=interaction.user.mention, inline=False)
            
            embed.add_field(name=texts['abs_field_dates'], value=f"📅 {self.start_date.value} ➔ {self.end_date.value}", inline=False)
            embed.add_field(name=texts['abs_field_duration'], value=f"⏱️ {duration_str}", inline=True)
            embed.add_field(name=texts['abs_field_reason'], value=f"📝 {self.reason.value}", inline=False)
            embed.set_footer(text=config.EMBED_FOOTER)
            
            content = f"<@&{self.direction_role_id}>" if self.direction_role_id else ""
            await interaction.channel.send(content=content, embed=embed)
            
            await interaction.response.send_message("✅", ephemeral=True)
        except ValueError:
            await interaction.response.send_message(texts['abs_error_format'], ephemeral=True)

# --- VUE HELP ---
class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = 'fr' 

    def get_embed(self, category=None):
        texts = config.TRANSLATIONS[self.lang]
        
        if self.lang == 'fr':
            cmds_user = (
                f"• **/sum** : Affiche vos statistiques personnelles (Temps total, moyenne...).",
                f"• **/sumall** : Affiche le classement global des heures du serveur.",
                f"• **/about** : Affiche les informations, le ping et les crédits du bot.",
                f"• **/feedback** : Ouvre un formulaire pour donner votre avis ou signaler un bug au développeur.",
                f"• **/absence** : Ouvre un formulaire pour déclarer une absence officielle (message public + mention Direction)."
            )
            cmds_admin = (
                f"• **/presence** : Affiche la liste en temps réel des agents en service (Snapshot).\n",
                f"• **/details [joueur]** : Affiche l'historique des 10 dernières sessions d'un joueur.\n",
                f"• **/close [joueur]** : Force la fin de service d'un joueur (s'il a oublié).\n",
                f"• **/edittime** : Permet d'ajouter ou retirer manuellement du temps (Heures/Minutes/Secondes).\n",
                f"• **/cancel [joueur]** : Annule une session en cours sans la sauvegarder (Suppression).\n",
                f"• **/remove_user** : Supprime définitivement toutes les données d'un joueur de la DB.\n",
                f"• **/reset_server** : Réinitialise les données du serveur (Choix : Semaine/Mois/Tout).\n",
                f"• **/setup** : Ouvre le panneau interactif de configuration du bot (Salons, Rôles, Langue)."
            )
        else: # EN
            cmds_user = (
                f"• **/sum** : View your personal statistics (Total time, average...).",
                f"• **/sumall** : View the global server leaderboard.",
                f"• **/about** : Display bot information, ping, and credits.",
                f"• **/feedback** : Opens a form to give your review or report a bug to the developer.",
                f"• **/absence** : Opens a form to declare an official absence (Public message + Direction mention)."
            )
            cmds_admin = (
                f"• **/presence** : View real-time list of agents on duty (Snapshot).\n",
                f"• **/details [user]** : Display the history of a player's last 10 sessions.\n",
                f"• **/close [user]** : Force end a player's service (if they forgot).\n",
                f"• **/edittime** : Manually add or remove time (Hours/Minutes/Seconds).\n",
                f"• **/cancel [user]** : Cancel a session without saving data (Deletion).\n",
                f"• **/remove_user** : Permanently delete a user's data from the DB.\n",
                f"• **/reset_server** : Reset server statistics (Choice: Week/Month/All).\n",
                f"• **/setup** : Open the interactive bot configuration panel (Channels, Roles, Language)."
            )

        if category == 'root':
            return discord.Embed(title=texts['help_title'], description=texts['help_desc'], color=config.BOT_COLOR)
        elif category == 'user':
            embed = discord.Embed(title=f"{texts['help_title']} - {texts['help_cat_user']}", description=texts['help_user_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Commandes / Commands", value="\n".join(cmds_user), inline=False)
            return embed
        elif category == 'admin':
            embed = discord.Embed(title=f"{texts['help_title']} - {texts['help_cat_admin']}", description=texts['help_admin_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Commandes / Commands", value="\n".join(cmds_admin), inline=False)
            return embed
        
        return discord.Embed(title="Help / Aide", description="🌍 Please select your language.\n🌍 Veuillez choisir votre langue.", color=config.BOT_COLOR)

    def update_buttons(self, state):
        self.clear_items()
        texts = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])

        if state == 'lang':
            b1 = discord.ui.Button(label="Français", emoji="🇫🇷", custom_id="lang_fr", style=discord.ButtonStyle.primary)
            b1.callback = self.cb_lang_fr
            b2 = discord.ui.Button(label="English", emoji="🇬🇧", custom_id="lang_en", style=discord.ButtonStyle.primary)
            b2.callback = self.cb_lang_en
            self.add_item(b1)
            self.add_item(b2)
        
        elif state == 'menu':
            b_user = discord.ui.Button(label=texts['help_cat_user'], style=discord.ButtonStyle.success, emoji="👤")
            b_user.callback = self.cb_cat_user
            b_admin = discord.ui.Button(label=texts['help_cat_admin'], style=discord.ButtonStyle.danger, emoji="🛡️")
            b_admin.callback = self.cb_cat_admin
            
            b_feedback = discord.ui.Button(label=texts['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1)
            b_feedback.callback = self.cb_feedback
            
            b_lang_back = discord.ui.Button(label=texts['help_back_lang'], emoji="🌍", style=discord.ButtonStyle.secondary, row=1)
            b_lang_back.callback = self.cb_back_to_lang
            
            self.add_item(b_user)
            self.add_item(b_admin)
            self.add_item(b_feedback)
            self.add_item(b_lang_back)
        
        elif state == 'sub':
            b_back = discord.ui.Button(label=texts['help_back'], style=discord.ButtonStyle.secondary, emoji="↩️")
            b_back.callback = self.cb_back
            self.add_item(b_back)

    async def cb_lang_fr(self, interaction: discord.Interaction):
        self.lang = 'fr'
        self.update_buttons('menu')
        await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_lang_en(self, interaction: discord.Interaction):
        self.lang = 'en'
        self.update_buttons('menu')
        await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_back_to_lang(self, interaction: discord.Interaction):
        self.update_buttons('lang')
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    async def cb_cat_user(self, interaction: discord.Interaction):
        self.update_buttons('sub')
        await interaction.response.edit_message(embed=self.get_embed('user'), view=self)
    async def cb_cat_admin(self, interaction: discord.Interaction):
        self.update_buttons('sub')
        await interaction.response.edit_message(embed=self.get_embed('admin'), view=self)
    async def cb_back(self, interaction: discord.Interaction):
        self.update_buttons('menu')
        await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_feedback(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=FeedbackView(self.bot, self.lang), ephemeral=True)

class AboutView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        self.add_item(discord.ui.Button(label=texts['btn_invite'], url=invite_url, style=discord.ButtonStyle.link, emoji="➕"))
        self.add_item(discord.ui.Button(label=texts['btn_source'], url=config.GITHUB_LINK, style=discord.ButtonStyle.url))
        
        if config.SUPPORT_LINK and "discord.gg" in config.SUPPORT_LINK:
            self.add_item(discord.ui.Button(label=texts['btn_support'], url=config.SUPPORT_LINK, style=discord.ButtonStyle.url))

        btn_fb = discord.ui.Button(label=texts['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1)
        btn_fb.callback = self.cb_feedback
        self.add_item(btn_fb)
        
        btn_ref = discord.ui.Button(label=texts['btn_refresh'], style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
        btn_ref.callback = self.cb_refresh
        self.add_item(btn_ref)

    async def cb_feedback(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=FeedbackView(self.bot, self.lang), ephemeral=True)

    async def cb_refresh(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"ℹ️ {config.BOT_NAME}", description="Service Bot", color=config.BOT_COLOR)
        embed.add_field(name="Version", value=f"`{config.BOT_VERSION}`", inline=True)
        embed.add_field(name="Dev", value=f"matteohooliga\n`({config.OWNER_ID})`", inline=True)
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.set_footer(text=config.EMBED_FOOTER)
        embed.timestamp = datetime.now()
        await interaction.response.edit_message(embed=embed, view=self)

class SetupView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.lang = 'fr'
        self.sel_lang = 'fr'
        self.sel_service = None
        self.sel_logs = None
        self.sel_role = None
        self.update_components()

    def update_components(self):
        self.clear_items()
        txt = config.TRANSLATIONS[self.sel_lang]

        lang_menu = discord.ui.Select(
            placeholder=txt['setup_ph_lang'],
            options=[
                discord.SelectOption(label="Français", value="fr", emoji="🇫🇷", default=(self.sel_lang=='fr')),
                discord.SelectOption(label="English", value="en", emoji="🇬🇧", default=(self.sel_lang=='en'))
            ], row=0
        )
        lang_menu.callback = self.cb_lang
        self.add_item(lang_menu)

        svc_menu = discord.ui.ChannelSelect(
            placeholder=txt['setup_ph_service'],
            channel_types=[discord.ChannelType.text],
            min_values=1, max_values=1, row=1
        )
        svc_menu.callback = self.cb_service
        self.add_item(svc_menu)

        log_menu = discord.ui.ChannelSelect(
            placeholder=txt['setup_ph_logs'],
            channel_types=[discord.ChannelType.text],
            min_values=0, max_values=1, row=2
        )
        log_menu.callback = self.cb_logs
        self.add_item(log_menu)

        role_menu = discord.ui.RoleSelect(
            placeholder=txt['setup_ph_role'],
            min_values=0, max_values=1, row=3
        )
        role_menu.callback = self.cb_role
        self.add_item(role_menu)

        btn = discord.ui.Button(label=txt['setup_btn_save'], style=discord.ButtonStyle.success, row=4)
        btn.callback = self.cb_save
        self.add_item(btn)

    async def cb_lang(self, interaction: discord.Interaction):
        self.sel_lang = interaction.data['values'][0]
        self.update_components()
        txt = config.TRANSLATIONS[self.sel_lang]
        embed = discord.Embed(title=txt['setup_panel_title'], description=txt['setup_panel_desc'], color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.edit_message(embed=embed, view=self)

    async def cb_service(self, interaction: discord.Interaction):
        self.sel_service = interaction.data['values'][0]
        await interaction.response.defer()

    async def cb_logs(self, interaction: discord.Interaction):
        self.sel_logs = interaction.data['values'][0] if interaction.data['values'] else None
        await interaction.response.defer()

    async def cb_role(self, interaction: discord.Interaction):
        self.sel_role = interaction.data['values'][0] if interaction.data['values'] else None
        await interaction.response.defer()

    async def cb_save(self, interaction: discord.Interaction):
        txt = config.TRANSLATIONS[self.sel_lang]
        if not self.sel_service: return await interaction.response.send_message(txt['setup_err_no_service'], ephemeral=True)
        
        await interaction.response.defer()
        guild = interaction.guild
        
        try:
            chan_svc = guild.get_channel(int(self.sel_service))
            chan_log = guild.get_channel(int(self.sel_logs)) if self.sel_logs else None
            role_dir = guild.get_role(int(self.sel_role)) if self.sel_role else None
            
            from views import ServiceButtonsView
            from utils import create_service_embed
            
            embed = create_service_embed([], guild, self.sel_lang)
            view = ServiceButtonsView(self.bot, self.sel_lang)
            msg = await chan_svc.send(embed=embed, view=view)
            
            await self.bot.db.set_guild_config(
                str(guild.id), str(chan_svc.id), str(msg.id),
                str(chan_log.id) if chan_log else None,
                self.sel_lang,
                str(role_dir.id) if role_dir else None
            )
            
            if chan_log:
                try:
                    embed_log = discord.Embed(title=txt['log_setup_title'], description=txt['log_setup_desc'], color=discord.Color.green())
                    embed_log.set_footer(text=config.EMBED_FOOTER)
                    await chan_log.send(embed=embed_log)
                except: pass

            await interaction.followup.send(txt['setup_success'].format(channel=chan_svc.mention), ephemeral=True)
            self.stop()
        except Exception as e: await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)

class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.refresh_service.start()

    def cog_unload(self):
        self.refresh_service.cancel()

    async def get_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        return data['language'] if data and data.get('language') else 'fr'

    @tasks.loop(seconds=10)
    async def refresh_service(self):
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                try:
                    guild_id = int(config_data['guild_id'])
                    active_sessions = await self.db.get_all_active_sessions(str(guild_id))
                    if not active_sessions: continue
                    await self.bot.update_service_message(guild_id, config_data)
                except Exception: continue
        except Exception: pass

    @refresh_service.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    async def close_user_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        active_sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        choices = []
        for session in active_sessions:
            if current.lower() in session['username'].lower():
                choices.append(app_commands.Choice(name=f"🟢 {session['username']}", value=session['user_id']))
        return choices[:25]

    # --- COMMANDES ---

    @app_commands.command(name="feedback", description="Donner un avis ou signaler un bug / Feedback")
    async def feedback(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        await interaction.response.send_message(view=FeedbackView(self.bot, lang), ephemeral=True)

    @app_commands.command(name="help", description="Menu d'aide / Help Menu")
    async def help(self, interaction: discord.Interaction):
        view = HelpView(self.bot)
        view.update_buttons('lang')
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    @app_commands.command(name="about", description="Info")
    async def about(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        view = AboutView(self.bot, lang)
        embed = discord.Embed(title=f"ℹ️ {config.BOT_NAME}", description="Service Bot", color=config.BOT_COLOR)
        embed.add_field(name="Version", value=f"`{config.BOT_VERSION}`", inline=True)
        embed.add_field(name="Dev", value=f"matteohooliga\n`({config.OWNER_ID})`", inline=True)
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="absence", description="Déclarer une absence / Declare absence")
    async def absence(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        direction_role_id = config_data.get('direction_role_id') if config_data else None
        await interaction.response.send_modal(AbsenceModal(self.bot, lang, direction_role_id))

    @app_commands.command(name="setup", description="Ouvrir le panneau de configuration / Open Setup Panel")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        view = SetupView(self.bot)
        embed = discord.Embed(
            title=config.TRANSLATIONS['fr']['setup_panel_title'],
            description=config.TRANSLATIONS['fr']['setup_panel_desc'],
            color=config.BOT_COLOR
        )
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="sum", description="Stats")
    async def sum(self, interaction: discord.Interaction, user: discord.User = None):
        lang = await self.get_lang(interaction.guild_id)
        target = user or interaction.user
        stats = await self.db.get_user_stats(str(target.id), str(interaction.guild_id))
        embed = create_stats_embed(stats, target, lang)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="sumall", description="Global stats")
    async def sumall(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        embed = create_all_stats_embed(all_stats, interaction.guild, lang)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="edittime", description="Edit time")
    @app_commands.choices(operation=[app_commands.Choice(name="+", value="add"), app_commands.Choice(name="-", value="remove")])
    @app_commands.default_permissions(manage_guild=True)
    async def edittime(self, interaction: discord.Interaction, user: discord.User, operation: app_commands.Choice[str], hours: int = 0, minutes: int = 0, seconds: int = 0):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        total_sec = (hours * 3600) + (minutes * 60) + seconds
        if total_sec <= 0: return await interaction.response.send_message("⚠️ > 0", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        ms = total_sec * 1000 * (1 if operation.value == "add" else -1)
        try:
            await self.db.add_time_adjustment(str(user.id), str(interaction.guild_id), user.display_name, ms)
            new_stats = await self.db.get_user_stats(str(user.id), str(interaction.guild_id))
            new_total = format_duration(new_stats['total_time'] or 0)
            action = texts['time_added'] if operation.value == "add" else texts['time_removed']
            val_fmt = format_duration(total_sec * 1000)
            msg = texts['edit_success'].format(user=user.mention, action=action.capitalize(), value=val_fmt, new_total=new_total)
            await interaction.followup.send(msg, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_edit_time'], "Admin modification.", discord.Color.blue(), [("Admin", interaction.user.mention), ("Cible", user.mention), (action, val_fmt), (texts['new_total'], new_total)])
        except Exception as e: await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)

    @app_commands.command(name="close", description="Close")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    async def close(self, interaction: discord.Interaction, user_id: str):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(texts['no_active_session'], ephemeral=True)
        try:
            u = interaction.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            mention = u.mention
        except: mention = f"<@{user_id}>"
        ended = await self.db.end_session(str(user_id), str(interaction.guild_id))
        if ended:
            dur = format_duration(ended['total_duration'])
            msg = texts['service_forced_stop'].format(user=mention, duration=dur)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild.id, texts['log_force_close'], "Admin Force Close", discord.Color.orange(), [("Cible", mention), ("Mod", interaction.user.mention)])
        else: await interaction.response.send_message("❌ Error", ephemeral=True)

    @app_commands.command(name="cancel", description="Cancel")
    async def cancel(self, interaction: discord.Interaction, user: discord.User = None):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        target = user or interaction.user
        if user and user != interaction.user and not interaction.permissions.manage_guild:
            return await interaction.response.send_message("⛔ Perms.", ephemeral=True)
        session = await self.db.get_active_session(str(target.id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(texts['service_not_started'], ephemeral=True)
        async with aiosqlite.connect(self.db.db_name) as db:
             await db.execute("DELETE FROM sessions WHERE id = ?", (session['id'],))
             await db.commit()
        await interaction.response.send_message("🗑️ Cancelled.", ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        await self.bot.send_log(interaction.guild.id, texts['log_cancel'], "User cancel", discord.Color.dark_red(), [("User", interaction.user.mention)])

    @app_commands.command(name="remove_user", description="Remove User")
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        await interaction.response.defer(ephemeral=True)
        deleted = await self.db.delete_user_data(str(interaction.guild_id), str(user.id))
        if deleted:
            await interaction.followup.send(f"🗑️ {deleted} sessions deleted.", ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild.id, texts.get('log_remove', "Remove User"), "Admin delete", discord.Color.dark_grey(), [("Target", user.mention)])
        else: await interaction.followup.send("⚠️ No data.", ephemeral=True)

    @app_commands.command(name="reset_server", description="Reset")
    @app_commands.choices(periode=[app_commands.Choice(name="Semaine", value="week"), app_commands.Choice(name="Mois", value="month"), app_commands.Choice(name="Tout", value="all")])
    async def reset_server(self, interaction: discord.Interaction, periode: app_commands.Choice[str]):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        await interaction.response.defer(ephemeral=True)
        active = await self.db.get_all_active_sessions(str(interaction.guild_id))
        for s in active: await self.db.end_session(s['user_id'], str(interaction.guild_id))
        ms = None
        if periode.value == "week": ms = 7 * 86400000
        elif periode.value == "month": ms = 30 * 86400000
        deleted = await self.db.reset_guild_data(str(interaction.guild_id), ms)
        await self.bot.update_service_message(interaction.guild_id)
        await interaction.followup.send(f"🧹 Reset: {deleted}", ephemeral=True)
        await self.bot.send_log(interaction.guild.id, texts['log_reset'], "Admin reset", discord.Color.red(), [("Admin", interaction.user.mention)])

    @app_commands.command(name="presence", description="Presence")
    async def presence(self, interaction: discord.Interaction):
        active = await self.db.get_all_active_sessions(str(interaction.guild_id))
        embed = create_service_embed(active, interaction.guild, await self.get_lang(interaction.guild_id))
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="details", description="Details")
    @app_commands.default_permissions(manage_guild=True)
    async def details(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=False)
        stats = await self.db.get_user_stats(str(user.id), str(interaction.guild_id))
        history = await self.db.get_last_sessions(str(user.id), str(interaction.guild_id), 10)
        if not stats or stats['total_sessions'] == 0: return await interaction.followup.send("❌ No data", ephemeral=False)
        embed = discord.Embed(title=f"📄 {user.display_name}", color=config.BOT_COLOR)
        embed.add_field(name="Total", value=f"`{format_duration(stats['total_time'] or 0)}`", inline=True)
        hist_text = ""
        for s in history:
            date = f"<t:{int(s['start_time']/1000)}:d>"
            dur = format_duration(s['total_duration'])
            icon = "📈" if s['start_time'] == s['end_time'] else "🔹"
            hist_text += f"{icon} {date} : `{dur}`\n"
        embed.add_field(name="History", value=hist_text or "Vide", inline=False)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))