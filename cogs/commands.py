import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from typing import List
from datetime import datetime, timedelta
from utils import create_stats_embed, create_all_stats_embed, create_service_embed, format_duration, create_server_stats_embed
import config
import json
import math
from views import PaginationView

# --- FEEDBACK ---
async def send_feedback_log(bot, interaction, title, color, fields):
    target_id = config.DEV_FEEDBACK_CHANNEL_ID
    channel = bot.get_channel(target_id)
    if channel is None:
        try: channel = await bot.fetch_channel(target_id)
        except: return False
    if channel:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        for name, value in fields: embed.add_field(name=name, value=value, inline=False)
        embed.add_field(name="Source", value=f"{interaction.guild.name} (`{interaction.guild.id}`)", inline=False)
        embed.set_footer(text=config.EMBED_FOOTER)
        role_mention = f"<@&{config.DEV_FEEDBACK_ROLE_ID}>"
        try:
            await channel.send(content=role_mention, embed=embed)
            return True
        except: return False
    return False

class ReviewModal(discord.ui.Modal):
    def __init__(self, bot, lang):
        self.bot = bot; self.lang = lang; texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_review_title'])
        self.subject = discord.ui.TextInput(label=texts['feedback_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.rating = discord.ui.TextInput(label=texts['fb_review_rating'], style=discord.TextStyle.short, placeholder="5", required=True, max_length=1)
        self.comment = discord.ui.TextInput(label=texts['fb_review_comment'], style=discord.TextStyle.paragraph, required=True, max_length=1000)
        self.add_item(self.subject); self.add_item(self.rating); self.add_item(self.comment)
    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try: stars = max(1, min(5, int(self.rating.value))); star_str = "⭐" * stars
        except: star_str = "❓"
        fields = [("📌 Sujet", f"**{self.subject.value}**"), (texts['fb_field_rating'], f"{star_str} ({self.rating.value}/5)"), ("💬 Commentaire", self.comment.value)]
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_review_title'], config.COLOR_ORANGE, fields)
        if success: await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else: await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class BugReportModal(discord.ui.Modal):
    def __init__(self, bot, lang):
        self.bot = bot; self.lang = lang; texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_bug_title'])
        self.subject = discord.ui.TextInput(label=texts['fb_bug_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.description = discord.ui.TextInput(label=texts['fb_bug_desc'], style=discord.TextStyle.paragraph, required=True, max_length=2000)
        self.media = discord.ui.TextInput(label=texts['fb_bug_media'], style=discord.TextStyle.short, required=False, placeholder="https://...")
        self.add_item(self.subject); self.add_item(self.description); self.add_item(self.media)
    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        fields = [("📌 Sujet", f"**{self.subject.value}**"), ("📝 Description", self.description.value)]
        if self.media.value: fields.append((texts['fb_field_media'], self.media.value))
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_bug_title'], config.COLOR_RED, fields)
        if success: await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else: await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class FeedbackTypeSelect(discord.ui.Select):
    def __init__(self, bot, lang):
        self.bot = bot; self.lang = lang; texts = config.TRANSLATIONS[lang]
        options = [discord.SelectOption(label=texts['fb_opt_review'], value="review", emoji="⭐"), discord.SelectOption(label=texts['fb_opt_bug'], value="bug", emoji="🐛")]
        super().__init__(placeholder=texts['fb_select_placeholder'], min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "review": await interaction.response.send_modal(ReviewModal(self.bot, self.lang))
        elif self.values[0] == "bug": await interaction.response.send_modal(BugReportModal(self.bot, self.lang))

class FeedbackView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=60); self.add_item(FeedbackTypeSelect(bot, lang))

# --- ABSENCE ---
class AbsenceModal(discord.ui.Modal):
    def __init__(self, bot, lang, direction_role_id):
        self.bot = bot; self.lang = lang; self.direction_role_id = direction_role_id; texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['abs_modal_title'])
        self.start_date = discord.ui.TextInput(label=texts['abs_start_label'], placeholder=texts['abs_start_ph'], max_length=10, required=True)
        self.end_date = discord.ui.TextInput(label=texts['abs_end_label'], placeholder=texts['abs_end_ph'], max_length=10, required=True)
        self.reason = discord.ui.TextInput(label=texts['abs_reason_label'], style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.start_date); self.add_item(self.end_date); self.add_item(self.reason)
    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            d1 = datetime.strptime(self.start_date.value, "%d/%m/%Y"); d2 = datetime.strptime(self.end_date.value, "%d/%m/%Y")
            if d2 < d1: return await interaction.response.send_message(texts['abs_error_logic'], ephemeral=True)
            delta = d2 - d1; days = delta.days + 1; duration_str = f"{days} jour(s)" if self.lang == 'fr' else f"{days} day(s)"
            embed = discord.Embed(title=texts['abs_embed_title'].format(user=interaction.user.display_name), color=config.COLOR_PURPLE, timestamp=datetime.now())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name=texts['abs_user_field'], value=interaction.user.mention, inline=False)
            embed.add_field(name=texts['abs_field_dates'], value=f"📅 {self.start_date.value} ➔ {self.end_date.value}", inline=False)
            embed.add_field(name=texts['abs_field_duration'], value=f"⏱️ {duration_str}", inline=True)
            embed.add_field(name=texts['abs_field_reason'], value=f"📝 {self.reason.value}", inline=False)
            embed.set_footer(text=config.EMBED_FOOTER)
            content = ""
            if self.direction_role_id:
                try:
                    roles = json.loads(self.direction_role_id)
                    content = " ".join([f"<@&{r}>" for r in roles])
                except: content = f"<@&{self.direction_role_id}>"
            msg = await interaction.channel.send(content=content, embed=embed)
            await msg.add_reaction("✅")
            await interaction.response.send_message("✅", ephemeral=True)
        except ValueError: await interaction.response.send_message(texts['abs_error_format'], ephemeral=True)

# --- EDIT TIME ---
class EditTimeModal(discord.ui.Modal):
    def __init__(self, bot, lang, target_user, operation):
        texts = config.TRANSLATIONS[lang]
        op_text = texts['time_added'] if operation == "add" else texts['time_removed']
        super().__init__(title=op_text)
        self.bot = bot; self.lang = lang; self.target_user = target_user; self.operation = operation
        self.hours = discord.ui.TextInput(label=texts['et_label_hours'], placeholder="0", required=False, default="0", max_length=3)
        self.minutes = discord.ui.TextInput(label=texts['et_label_minutes'], placeholder="0", required=False, default="0", max_length=2)
        self.seconds = discord.ui.TextInput(label=texts['et_label_seconds'], placeholder="0", required=False, default="0", max_length=2)
        self.add_item(self.hours); self.add_item(self.minutes); self.add_item(self.seconds)
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
            embed = discord.Embed(title=texts['edit_success'].format(user=self.target_user.display_name, action="", value="", new_total="").split('\n')[0], color=config.COLOR_PURPLE)
            embed.description = texts['edit_desc'].format(user=self.target_user.mention)
            embed.add_field(name=texts['edit_field_action'], value=action_str, inline=True)
            embed.add_field(name=texts['edit_field_amount'], value=f"`{val_fmt}`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name=texts['edit_field_old'], value=f"`{old_total}`", inline=True)
            embed.add_field(name="➡️", value=" ", inline=True)
            embed.add_field(name=texts['edit_field_new_total'], value=f"`{new_total}`", inline=True)
            embed.set_footer(text=config.EMBED_FOOTER)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_edit_time_title'], texts['log_edit_time_desc'].format(admin=interaction.user.mention), config.COLOR_BLUE, [(texts['edit_field_admin'], interaction.user.mention), (texts['edit_field_target'], self.target_user.mention), (texts['edit_field_action'], action_str), (texts['edit_field_amount'], val_fmt), (texts['edit_field_new_total'], new_total)])
        except Exception as e: await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class EditTimeView(discord.ui.View):
    def __init__(self, bot, lang, target_user):
        super().__init__(timeout=60)
        self.bot = bot; self.lang = lang; self.target_user = target_user
        texts = config.TRANSLATIONS[lang]
        self.add_item(discord.ui.Button(label=texts['et_btn_add'], emoji="➕", style=discord.ButtonStyle.success, custom_id="add"))
        self.add_item(discord.ui.Button(label=texts['et_btn_remove'], emoji="➖", style=discord.ButtonStyle.danger, custom_id="remove"))
    async def interaction_check(self, interaction: discord.Interaction):
        op = interaction.data['custom_id']
        await interaction.response.send_modal(EditTimeModal(self.bot, self.lang, self.target_user, op))
        return False

# --- VUES ---
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

class AboutView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
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
        txt = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        embed.add_field(name=txt['about_maint_title'], value=txt['about_maint_desc'], inline=False)
        embed.add_field(name="Ping", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
        embed.set_footer(text=config.EMBED_FOOTER)
        embed.timestamp = datetime.now()
        await interaction.response.edit_message(embed=embed, view=self)

class GoalModal(discord.ui.Modal):
    def __init__(self, parent_view, txt):
        super().__init__(title=txt['setup_ph_goal'])
        self.view = parent_view; self.txt = txt
        val = str(int(parent_view.sel_goal / 3600000)) if parent_view.sel_goal else ""
        self.goal = discord.ui.TextInput(label="Heures / Hours", placeholder="0 = OFF", required=True, default=val)
        self.add_item(self.goal)
    async def on_submit(self, interaction: discord.Interaction):
        try: hours = int(self.goal.value); ms_goal = hours * 3600 * 1000
        except: ms_goal = 0
        await interaction.response.defer()
        guild = interaction.guild
        try:
            chan_svc = guild.get_channel(int(self.view.sel_service))
            chan_log = guild.get_channel(int(self.view.sel_logs)) if self.view.sel_logs else None
            role_dir = json.dumps(self.view.sel_role) if self.view.sel_role else None
            role_auto = json.dumps(self.view.sel_autorole) if self.view.sel_autorole else None
            from views import ServiceButtonsView
            from utils import create_service_embed
            embed = create_service_embed([], guild, self.view.sel_lang)
            view = ServiceButtonsView(self.view.bot, self.view.sel_lang)
            msg = await chan_svc.send(embed=embed, view=view)
            await self.view.bot.db.set_guild_config(str(guild.id), str(chan_svc.id), str(msg.id), str(chan_log.id) if chan_log else None, self.view.sel_lang, str(role_dir) if role_dir else None, ms_goal, role_auto)
            if chan_log:
                try: await chan_log.send(embed=discord.Embed(title=self.txt['log_setup_title'], description=self.txt['log_setup_desc'], color=config.COLOR_GREEN))
                except: pass
            await interaction.followup.send(self.txt['setup_success'].format(channel=chan_svc.mention), ephemeral=True)
            self.view.stop()
        except Exception as e: await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)

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
        txt = config.TRANSLATIONS[self.sel_lang]
        if not self.sel_service: return await interaction.response.send_message(txt['setup_err_no_service'], ephemeral=True)
        await interaction.response.send_modal(GoalModal(self, txt))
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

    # --- GLOBAL BLACKLIST CHECK ---
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if await self.bot.db.is_blacklisted(str(interaction.user.id)):
            await interaction.response.send_message(config.TRANSLATIONS['fr']['bl_error'], ephemeral=True)
            return False
        return True

    @tasks.loop(seconds=10)
    async def refresh_service(self):
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                try:
                    guild_id = int(config_data['guild_id'])
                    active_sessions = await self.db.get_all_active_sessions(str(guild_id))
                    # Si personne en service, on skip pour ne pas spammer l'API
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
        await view.refresh(interaction, self.bot)

    @app_commands.command(name="absence", description="Déclarer une absence / Declare absence")
    async def absence(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        raw = config_data.get('direction_role_id') if config_data else None
        try: role_ids = json.loads(raw) if raw else []
        except: role_ids = [raw] if raw else []
        await interaction.response.send_modal(AbsenceModal(self.bot, lang, role_ids))

    @app_commands.command(name="setup", description="Ouvrir le panneau de configuration / Open Setup Panel")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        view = SetupView(self.bot, config_data)
        lang = config_data.get('language', 'fr') if config_data else 'fr'
        txt = config.TRANSLATIONS[lang]
        embed = discord.Embed(title=txt['setup_panel_title'], description=view.get_desc(txt), color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="sum", description="Stats")
    async def sum(self, interaction: discord.Interaction, user: discord.User = None):
        lang = await self.get_lang(interaction.guild_id)
        target = user or interaction.user
        stats = await self.db.get_user_stats(str(target.id), str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        goal = conf.get('min_hours_goal', 0) if conf else 0
        embed = create_stats_embed(stats, target, lang, goal)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="sumall", description="Global stats")
    async def sumall(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        goal = conf.get('min_hours_goal', 0) if conf else 0
        from utils import create_all_stats_embed 
        embed, total_pages = create_all_stats_embed(all_stats, interaction.guild, lang, 1, goal)
        if total_pages > 1:
            view = PaginationView(self.bot, all_stats, interaction.guild, lang, goal)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        else: await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="edittime", description="Edit time")
    @app_commands.default_permissions(manage_guild=True)
    async def edittime(self, interaction: discord.Interaction, user: discord.User):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        view = EditTimeView(self.bot, lang, user)
        embed = discord.Embed(title=txt['et_view_title'], description=txt['et_view_desc'].format(user=user.display_name), color=config.BOT_COLOR)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="close", description="Close")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(administrator=True) # ADMIN ONLY
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
            await self.bot.send_log(interaction.guild.id, texts['log_force_close_title'], texts['log_force_close_desc'].format(admin=interaction.user.mention, user=mention), config.COLOR_ORANGE)
        else: await interaction.response.send_message("❌ Error", ephemeral=True)

    @app_commands.command(name="cancel", description="Cancel")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(administrator=True) # ADMIN ONLY
    async def cancel(self, interaction: discord.Interaction, user_id: str):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(texts['service_not_started'], ephemeral=True)
        try:
            u = interaction.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            mention = u.mention
        except: mention = f"<@{user_id}>"
        async with aiosqlite.connect(self.db.db_name) as db:
             await db.execute("DELETE FROM sessions WHERE id = ?", (session['id'],))
             await db.commit()
        await interaction.response.send_message(texts['cancel_success'], ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        await self.bot.send_log(interaction.guild.id, texts['log_cancel_title'], texts['log_cancel_desc'].format(admin=interaction.user.mention, user=mention), config.COLOR_RED)

    @app_commands.command(name="remove_user", description="Remove User")
    @app_commands.default_permissions(administrator=True)
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(texts['error_perms'], ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        deleted = await self.db.delete_user_data(str(interaction.guild_id), str(user.id))
        if deleted:
            await interaction.followup.send(f"🗑️ {deleted} sessions deleted.", ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild.id, texts['log_remove_title'], texts['log_remove_desc'].format(admin=interaction.user.mention, user=user.mention), config.COLOR_RED)
        else: await interaction.followup.send("⚠️ No data.", ephemeral=True)

    @app_commands.command(name="reset_server", description="Reset")
    @app_commands.choices(periode=[app_commands.Choice(name="Semaine", value="week"), app_commands.Choice(name="Mois", value="month"), app_commands.Choice(name="Tout", value="all")])
    @app_commands.default_permissions(administrator=True)
    async def reset_server(self, interaction: discord.Interaction, periode: app_commands.Choice[str]):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(texts['error_perms'], ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        active = await self.db.get_all_active_sessions(str(interaction.guild_id))
        for s in active: await self.db.end_session(s['user_id'], str(interaction.guild_id))
        ms = None
        if periode.value == "week": ms = 7 * 86400000
        elif periode.value == "month": ms = 30 * 86400000
        deleted = await self.db.reset_guild_data(str(interaction.guild_id), ms)
        await self.bot.update_service_message(interaction.guild_id)
        await interaction.followup.send(f"🧹 Reset: {deleted}", ephemeral=True)
        await self.bot.send_log(interaction.guild.id, texts['log_reset_title'], texts['log_reset_desc'].format(admin=interaction.user.mention), config.COLOR_RED)

    @app_commands.command(name="presence", description="Presence")
    @app_commands.default_permissions(administrator=True) # ADMIN ONLY
    async def presence(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        
        if channel:
            try:
                message = [m async for m in channel.history(limit=1)][0]
            except IndexError:
                return await interaction.response.send_message(texts['error_no_message'], ephemeral=True)
            except Exception:
                return await interaction.response.send_message(texts['error_channel_type'], ephemeral=True)

            embed = discord.Embed(title=texts['pres_react_title'], description=texts['pres_react_desc'].format(channel=channel.mention), color=config.BOT_COLOR)
            found = False
            
            for reaction in message.reactions:
                users = []
                async for user in reaction.users():
                    if not user.bot: users.append(user.mention)
                
                if users:
                    found = True
                    embed.add_field(name=f"{str(reaction.emoji)} ({len(users)})", value=", ".join(users), inline=False)
            
            if not found: return await interaction.response.send_message(texts['pres_react_empty'], ephemeral=True)
            embed.set_footer(text=config.EMBED_FOOTER)
            await interaction.response.send_message(embed=embed)
        else:
            active = await self.db.get_all_active_sessions(str(interaction.guild_id))
            embed = create_service_embed(active, interaction.guild, lang)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="pauselist", description="Voir la liste des agents en pause")
    @app_commands.default_permissions(manage_guild=True)
    async def pauselist(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        
        sessions = await self.db.get_all_active_sessions(str(interaction.guild_id))
        paused_list = [s for s in sessions if s['is_paused']]

        if not paused_list:
            return await interaction.response.send_message(texts.get('paused_list_empty', "✅ Personne en pause."), ephemeral=True)

        desc = ""
        for s in paused_list:
            time_str = f"<t:{int(s['pause_start']/1000)}:R>"
            desc += f"• <@{s['user_id']}> ({time_str})\n"

        embed = discord.Embed(
            title=texts.get('paused_list_title', "⏸️ Agents en Pause"), 
            description=desc, 
            color=config.COLOR_ORANGE
        )
        embed.set_footer(text=config.EMBED_FOOTER)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="server_stats", description="Statistiques avancées du serveur")
    @app_commands.default_permissions(administrator=True)
    async def server_stats(self, interaction: discord.Interaction):
        lang = await self.get_lang(interaction.guild_id)
        from utils import create_server_stats_embed
        stats = await self.db.get_advanced_server_stats(str(interaction.guild_id))
        
        if not stats:
            return await interaction.response.send_message(config.TRANSLATIONS[lang]['stats_no_data'], ephemeral=True)
            
        embed = create_server_stats_embed(stats, stats['days_analyzed'], lang)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="details", description="Details")
    @app_commands.default_permissions(manage_guild=True)
    async def details(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=False)
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        stats = await self.db.get_user_stats(str(user.id), str(interaction.guild_id))
        history = await self.db.get_last_sessions(str(user.id), str(interaction.guild_id), 10)
        if not stats or stats['total_sessions'] == 0: return await interaction.followup.send("❌ No data", ephemeral=False)
        embed = discord.Embed(title=f"📄 {user.display_name}", color=config.BOT_COLOR)
        embed.add_field(name="Total", value=f"`{format_duration(stats['total_time'] or 0)}`", inline=True)
        avg = format_duration(stats['avg_time'] or 0)
        embed.add_field(name="Moyenne", value=f"`{avg}`", inline=True)
        hist_text = ""
        for s in history:
            date = f"<t:{int(s['start_time']/1000)}:d>"
            dur = format_duration(s['total_duration'])
            if s['start_time'] == s['end_time']:
                icon = "🔧"
                t = txt['det_type_adjust']
                dur = f"+{dur}" if s['total_duration'] > 0 else dur
            else:
                icon = "🟢"
                t = txt['det_type_service']
            hist_text += f"{icon} **{date}** • {t} : `{dur}`\n"
        embed.add_field(name="History", value=hist_text or "Vide", inline=False)
        embed.set_footer(text=config.EMBED_FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=False)
        
    @app_commands.command(name="auto_role", description="Donner le rôle auto")
    @app_commands.default_permissions(administrator=True)
    async def auto_role(self, interaction: discord.Interaction, user: discord.Member):
        lang = await self.get_lang(interaction.guild_id)
        txt = config.TRANSLATIONS[lang]
        conf = await self.db.get_guild_config(str(interaction.guild_id))
        if not conf or not conf.get('auto_roles_list'): return await interaction.response.send_message(txt['error_no_role'], ephemeral=True)
        try:
            role_ids = json.loads(conf['auto_roles_list'])
            added = []
            for rid in role_ids:
                r = interaction.guild.get_role(int(rid))
                if r:
                    await user.add_roles(r)
                    added.append(r.mention)
            if added:
                msg = txt['role_added'].format(role=", ".join(added), user=user.mention)
                await interaction.response.send_message(msg, ephemeral=True)
                await self.bot.send_log(interaction.guild.id, txt['log_autorole_title'], txt['log_autorole_desc'].format(admin=interaction.user.mention, user=user.mention), config.COLOR_GREEN)
            else: await interaction.response.send_message(txt['error_no_role'], ephemeral=True)
        except Exception as e: await interaction.response.send_message(f"❌ Erreur: `{e}`", ephemeral=True)

    @app_commands.command(name="pause", description="Mettre en pause/reprendre le service d'un joueur")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def pause(self, interaction: discord.Interaction, user_id: str):
        lang = await self.get_lang(interaction.guild_id)
        texts = config.TRANSLATIONS[lang]
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(texts['no_active_session'], ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        try:
            u = interaction.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            mention = u.mention
        except: mention = f"<@{user_id}>"
        if session['is_paused']:
            await self.db.resume_session(str(user_id), str(interaction.guild_id))
            await interaction.followup.send(texts['admin_resume_success'].format(user=mention), ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_admin_resume_title'], texts['log_admin_resume_desc'].format(admin=interaction.user.mention, user=mention), config.COLOR_BLUE)
        else:
            await self.db.pause_session(str(user_id), str(interaction.guild_id))
            await interaction.followup.send(texts['admin_pause_success'].format(user=mention), ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_admin_pause_title'], texts['log_admin_pause_desc'].format(admin=interaction.user.mention, user=mention), config.COLOR_ORANGE)
        await self.bot.update_service_message(interaction.guild_id)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))