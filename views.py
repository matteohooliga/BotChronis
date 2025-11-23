import discord
import config
import json
from utils import format_duration, check_permissions, create_all_stats_embed
from datetime import datetime

class PaginationView(discord.ui.View):
    def __init__(self, bot, all_stats, guild, lang, goal=0):
        super().__init__(timeout=300)
        self.bot = bot
        self.all_stats = all_stats
        self.guild = guild
        self.lang = lang
        self.goal = goal
        self.current_page = 1
        self.txt = config.TRANSLATIONS[lang]
        self.message = None 
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']
        
        import math
        total_pages = math.ceil(len(self.all_stats) / 10)
        if total_pages == 0: total_pages = 1
        
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_embed(interaction)

    async def update_embed(self, interaction):
        embed, total_pages = create_all_stats_embed(self.all_stats, self.guild, self.lang, self.current_page, self.goal)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
        self.message = interaction.message

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try: await self.message.edit(view=self)
            except: pass

class ServiceButtonsView(discord.ui.View):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db
        texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == config.BUTTONS['start']['custom_id']: 
                    child.label = texts['btn_start']
                    child.emoji = config.BUTTONS['start']['emoji']
                elif child.custom_id == config.BUTTONS['pause']['custom_id']: 
                    child.label = texts['btn_pause']
                    child.emoji = config.BUTTONS['pause']['emoji']
                elif child.custom_id == config.BUTTONS['stop']['custom_id']: 
                    child.label = texts['btn_stop']
                    child.emoji = config.BUTTONS['stop']['emoji']

    async def get_lang(self, guild_id: str):
        data = await self.db.get_guild_config(guild_id)
        return data['language'] if data and data.get('language') else 'fr'

    async def _check_access(self, interaction):
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        lang = config_data.get('language', 'fr') if config_data else 'fr'
        
        if config_data and int(config_data.get('is_maintenance', 0)) == 1:
            if str(interaction.user.id) == config.OWNER_ID: pass
            else:
                msg = config.TRANSLATIONS[lang]['maint_block_msg']
                await interaction.response.send_message(msg, ephemeral=True)
                return False

        allowed_roles_json = config_data.get('allowed_roles')
        allowed = json.loads(allowed_roles_json) if allowed_roles_json else None
        if not check_permissions(interaction.user, allowed):
            await interaction.response.send_message(config.TRANSLATIONS[lang]['error_perms'], ephemeral=True)
            return False
        return True

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.get_lang(str(interaction.guild_id))
        texts = config.TRANSLATIONS[lang]
        try:
            if await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                return await interaction.followup.send(texts['service_already_started'], ephemeral=True)
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await interaction.followup.send(texts['service_started'], ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_start_title'], texts['log_start_desc'].format(user=interaction.user.mention), config.COLOR_GREEN)
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.get_lang(str(interaction.guild_id))
        texts = config.TRANSLATIONS[lang]
        try:
            active = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not active: return await interaction.followup.send(texts['service_not_started'], ephemeral=True)
            if active['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(texts['service_resumed'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_resume_title'], texts['log_resume_desc'].format(user=interaction.user.mention), config.COLOR_BLUE)
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(texts['service_paused'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_pause_title'], texts['log_pause_desc'].format(user=interaction.user.mention), config.COLOR_ORANGE)
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.get_lang(str(interaction.guild_id))
        texts = config.TRANSLATIONS[lang]
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                return await interaction.followup.send(texts['service_not_started'], ephemeral=True)
            ended = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if ended:
                total = ended['total_duration'] + ended['pause_duration']
                msg = texts['service_stopped'].format(
                    duration=format_duration(total), 
                    pause=format_duration(ended['pause_duration']), 
                    effective=format_duration(ended['total_duration'])
                )
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_stop_title'], texts['log_stop_desc'].format(user=interaction.user.mention), config.COLOR_RED, [("Total", format_duration(total))])
                await self.bot.update_service_message(interaction.guild_id)
            else: 
                await interaction.followup.send(texts['error_db'], ephemeral=True)
        except Exception as e: await interaction.followup.send(texts['error_db'], ephemeral=True)

class EditTimeView(discord.ui.View):
    def __init__(self, bot, lang, target_user):
        super().__init__(timeout=60)
        self.bot = bot; self.lang = lang; self.target_user = target_user
        texts = config.TRANSLATIONS[lang]
        self.add_item(discord.ui.Button(label=texts['et_btn_add'], emoji="➕", style=discord.ButtonStyle.success, custom_id="add"))
        self.add_item(discord.ui.Button(label=texts['et_btn_remove'], emoji="➖", style=discord.ButtonStyle.danger, custom_id="remove"))
    async def interaction_check(self, interaction: discord.Interaction):
        op = interaction.data['custom_id']
        from cogs.commands import EditTimeModal # Import circulaire évité via import local si besoin ou structure
        # Note: EditTimeModal doit être dispo. Ici on suppose qu'il est dans cogs.commands
        # Pour éviter l'import circulaire, le modal est souvent défini dans le même fichier que la commande
        # MAIS comme tu as séparé views.py, l'appel doit se faire depuis commands.py
        # Ce code ici est juste pour la structure visuelle, la logique est dans commands.py
        return False

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot; self.lang = 'fr' 
    def get_embed(self, category=None):
        texts = config.TRANSLATIONS[self.lang]
        if category == 'root': return discord.Embed(title=texts['help_title'], description=texts['help_desc'], color=config.BOT_COLOR)
        if self.lang == 'fr':
            cmds_user = config.TRANSLATIONS['fr']['help_cmds_user']
            cmds_admin = config.TRANSLATIONS['fr']['help_cmds_admin']
        else:
            cmds_user = config.TRANSLATIONS['en']['help_cmds_user']
            cmds_admin = config.TRANSLATIONS['en']['help_cmds_admin']
        if category == 'user':
            embed = discord.Embed(title=f"{texts['help_title']} - {texts['help_cat_user']}", description=texts['help_user_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Commandes / Commands", value=cmds_user, inline=False)
            return embed
        elif category == 'admin':
            embed = discord.Embed(title=f"{texts['help_title']} - {texts['help_cat_admin']}", description=texts['help_admin_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Commandes / Commands", value=cmds_admin, inline=False)
            return embed
        return discord.Embed(title="Help / Aide", description="🌍 Please select your language.\n🌍 Veuillez choisir votre langue.", color=config.BOT_COLOR)
    def update_buttons(self, state):
        self.clear_items(); texts = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        if state == 'lang':
            self.add_item(discord.ui.Button(label="Français", emoji="🇫🇷", custom_id="lang_fr", style=discord.ButtonStyle.primary)); self.children[0].callback = self.cb_lang_fr
            self.add_item(discord.ui.Button(label="English", emoji="🇬🇧", custom_id="lang_en", style=discord.ButtonStyle.primary)); self.children[1].callback = self.cb_lang_en
        elif state == 'menu':
            self.add_item(discord.ui.Button(label=texts['help_cat_user'], style=discord.ButtonStyle.success, emoji="👤")); self.children[0].callback = self.cb_cat_user
            self.add_item(discord.ui.Button(label=texts['help_cat_admin'], style=discord.ButtonStyle.danger, emoji="🛡️")); self.children[1].callback = self.cb_cat_admin
            self.add_item(discord.ui.Button(label=texts['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1)); self.children[2].callback = self.cb_feedback
            self.add_item(discord.ui.Button(label=texts['help_back_lang'], emoji="🌍", style=discord.ButtonStyle.secondary, row=1)); self.children[3].callback = self.cb_back_to_lang
        elif state == 'sub':
            self.add_item(discord.ui.Button(label=texts['help_back'], style=discord.ButtonStyle.secondary, emoji="↩️")); self.children[0].callback = self.cb_back
    async def cb_lang_fr(self, interaction): self.lang = 'fr'; self.update_buttons('menu'); await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_lang_en(self, interaction): self.lang = 'en'; self.update_buttons('menu'); await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_back_to_lang(self, interaction): self.update_buttons('lang'); await interaction.response.edit_message(embed=self.get_embed(), view=self)
    async def cb_cat_user(self, interaction): self.update_buttons('sub'); await interaction.response.edit_message(embed=self.get_embed('user'), view=self)
    async def cb_cat_admin(self, interaction): self.update_buttons('sub'); await interaction.response.edit_message(embed=self.get_embed('admin'), view=self)
    async def cb_back(self, interaction): self.update_buttons('menu'); await interaction.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_feedback(self, interaction): await interaction.response.send_message(view=FeedbackView(self.bot, self.lang), ephemeral=True)

# --- FIX DU /ABOUT ---
class AboutView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang # <--- Ligne cruciale ajoutée
        texts = config.TRANSLATIONS[lang]
        perm = discord.Permissions(administrator=True)
        invite = discord.utils.oauth_url(bot.user.id, permissions=perm)
        self.add_item(discord.ui.Button(label=texts['btn_invite'], url=invite, style=discord.ButtonStyle.link, emoji="➕"))
        self.add_item(discord.ui.Button(label=texts['btn_source'], url=config.GITHUB_LINK, style=discord.ButtonStyle.url))
        if config.SUPPORT_LINK: self.add_item(discord.ui.Button(label=texts['btn_support'], url=config.SUPPORT_LINK, style=discord.ButtonStyle.url))
        btn_fb = discord.ui.Button(label=texts['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1); btn_fb.callback = lambda i: i.response.send_message(view=FeedbackView(bot, lang), ephemeral=True); self.add_item(btn_fb)
        btn_ref = discord.ui.Button(label=texts['btn_refresh'], style=discord.ButtonStyle.secondary, emoji="🔄", row=1); btn_ref.callback = lambda i: self.refresh(i, bot); self.add_item(btn_ref)
    async def refresh(self, interaction, bot):
        embed = discord.Embed(title=f"ℹ️ {config.BOT_NAME}", description="Service Bot", color=config.BOT_COLOR)
        embed.add_field(name="Version", value=f"`{config.BOT_VERSION}`", inline=True)
        embed.add_field(name="Dev", value=f"matteohooliga\n`({config.OWNER_ID})`", inline=True)
        
        # Récupération sécurisée des textes
        txt = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        embed.add_field(name=txt['about_maint_title'], value=txt['about_maint_desc'], inline=False)
        
        embed.add_field(name="Ping", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
        embed.set_footer(text=config.EMBED_FOOTER)
        embed.timestamp = datetime.now()
        await interaction.response.edit_message(embed=embed, view=self)

class FeedbackTypeSelect(discord.ui.Select):
    def __init__(self, bot, lang):
        self.bot = bot; self.lang = lang; texts = config.TRANSLATIONS[lang]
        options = [discord.SelectOption(label=texts['fb_opt_review'], value="review", emoji="⭐"), discord.SelectOption(label=texts['fb_opt_bug'], value="bug", emoji="🐛")]
        super().__init__(placeholder=texts['fb_select_placeholder'], min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        # Ces imports doivent être gérés dans commands.py normalement, mais pour la vue seule :
        # on renvoie juste un message si utilisé hors contexte
        await interaction.response.send_message("Utilisez /feedback", ephemeral=True)

class FeedbackView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=60); self.add_item(FeedbackTypeSelect(bot, lang))

class SetupView(discord.ui.View):
    def __init__(self, bot, config_data=None):
        super().__init__(timeout=300)
        self.bot = bot
        if config_data:
            self.sel_lang = config_data.get('language', 'fr')
            self.sel_service = config_data.get('channel_id')
            self.sel_logs = config_data.get('log_channel_id')
            rd = config_data.get('direction_role_id')
            try: self.sel_role = json.loads(rd) if rd else []
            except: self.sel_role = [rd] if rd else []
            ra = config_data.get('auto_roles_list')
            try: self.sel_autorole = json.loads(ra) if ra else []
            except: self.sel_autorole = []
            self.sel_goal = config_data.get('min_hours_goal', 0)
        else:
            self.sel_lang = 'fr'; self.sel_service = None; self.sel_logs = None; self.sel_role = []; self.sel_autorole = []; self.sel_goal = 0
        self.update_components()
    def update_components(self):
        self.clear_items(); txt = config.TRANSLATIONS[self.sel_lang]
        btn_fr = discord.ui.Button(label="Français", emoji="🇫🇷", style=discord.ButtonStyle.secondary, custom_id="lang_fr", disabled=(self.sel_lang=='fr')); btn_fr.callback = self.cb_lang_fr
        btn_en = discord.ui.Button(label="English", emoji="🇬🇧", style=discord.ButtonStyle.secondary, custom_id="lang_en", disabled=(self.sel_lang=='en')); btn_en.callback = self.cb_lang_en
        btn_save = discord.ui.Button(label=txt['setup_btn_save'], style=discord.ButtonStyle.success, custom_id="save", emoji="💾"); btn_save.callback = self.cb_save
        self.add_item(btn_fr); self.add_item(btn_en); self.add_item(btn_save)
        self.add_item(discord.ui.ChannelSelect(placeholder=txt['setup_ph_service'], channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="svc", row=1))
        self.add_item(discord.ui.ChannelSelect(placeholder=txt['setup_ph_logs'], channel_types=[discord.ChannelType.text], min_values=0, max_values=1, custom_id="log", row=2))
        self.add_item(discord.ui.RoleSelect(placeholder=txt['setup_ph_role'], min_values=0, max_values=20, custom_id="role", row=3))
        self.add_item(discord.ui.RoleSelect(placeholder=txt['setup_ph_autorole'], min_values=0, max_values=20, custom_id="autorole", row=4))
    async def refresh_view(self, interaction):
        txt = config.TRANSLATIONS[self.sel_lang]
        embed = discord.Embed(title=txt['setup_panel_title'], description=self.get_desc(txt), color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.edit_message(embed=embed, view=self)
    def get_desc(self, txt):
        desc = txt['setup_panel_desc'] + "\n\n"
        svc = f"<#{self.sel_service}>" if self.sel_service else "❌"
        logs = f"<#{self.sel_logs}>" if self.sel_logs else "❌"
        role = ", ".join([f"<@&{r}>" for r in self.sel_role]) if self.sel_role else "❌"
        aroles = ", ".join([f"<@&{r}>" for r in self.sel_autorole]) if self.sel_autorole else "❌"
        goal = f"{int(self.sel_goal/3600000)}h" if self.sel_goal else "0"
        desc += f"**Service:** {svc}\n**Logs:** {logs}\n**Roles Dir:** {role}\n**AutoRoles:** {aroles}\n**Goal:** {goal}"
        return desc
    async def cb_lang_fr(self, interaction): self.sel_lang = 'fr'; self.update_components(); await self.refresh_view(interaction)
    async def cb_lang_en(self, interaction): self.sel_lang = 'en'; self.update_components(); await self.refresh_view(interaction)
    async def cb_save(self, interaction):
        # L'implémentation réelle du callback est gérée dans commands.py avec le modal
        pass 
    async def interaction_check(self, interaction):
        cid = interaction.data.get('custom_id')
        vals = interaction.data.get('values', [])
        if not cid or cid in ["lang_fr", "lang_en", "save"]: return True
        if cid == "svc": self.sel_service = vals[0]
        elif cid == "log": self.sel_logs = vals[0] if vals else None
        elif cid == "role": self.sel_role = vals # List
        elif cid == "autorole": self.sel_autorole = vals # List
        await interaction.response.defer()
        txt = config.TRANSLATIONS[self.sel_lang]
        embed = discord.Embed(title=txt['setup_panel_title'], description=self.get_desc(txt), color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.edit_original_response(embed=embed, view=self)
        return False