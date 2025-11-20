import discord
import config
import json
from utils import format_duration, check_permissions, create_all_stats_embed
from datetime import datetime

class PaginationView(discord.ui.View):
    def __init__(self, bot, all_stats, guild, lang):
        super().__init__(timeout=60)
        self.bot = bot
        self.all_stats = all_stats
        self.guild = guild
        self.lang = lang
        self.current_page = 1
        self.txt = config.TRANSLATIONS[lang]
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_embed(interaction)

    async def update_embed(self, interaction):
        embed, total_pages = create_all_stats_embed(self.all_stats, self.guild, self.lang, self.current_page)
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

class ServiceButtonsView(discord.ui.View):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db
        texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == config.BUTTONS['start']['custom_id']: child.label = texts['btn_start']
                elif child.custom_id == config.BUTTONS['pause']['custom_id']: child.label = texts['btn_pause']
                elif child.custom_id == config.BUTTONS['stop']['custom_id']: child.label = texts['btn_stop']

    async def get_lang(self, guild_id: str):
        data = await self.db.get_guild_config(guild_id)
        return data['language'] if data and data.get('language') else 'fr'

    async def _check_access(self, interaction):
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        
        # CHECK MAINTENANCE
        if config_data and config_data.get('is_maintenance') == 1:
            lang = config_data.get('language', 'fr')
            await interaction.response.send_message(config.TRANSLATIONS[lang]['maint_block_msg'], ephemeral=True)
            return False

        allowed = json.loads(config_data['allowed_roles']) if config_data and config_data.get('allowed_roles') else None
        if not check_permissions(interaction.user, allowed):
            await interaction.response.send_message(config.TRANSLATIONS['fr']['error_perms'], ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Start", emoji=config.BUTTONS['start']['emoji'], style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
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
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild.id, texts['log_start_title'], texts['log_start_desc'].format(user=interaction.user.mention), config.COLOR_GREEN)
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(label="Pause", emoji=config.BUTTONS['pause']['emoji'], style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
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
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(label="Stop", emoji=config.BUTTONS['stop']['emoji'], style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
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
                msg = texts['service_stopped'].format(duration=format_duration(total), pause=format_duration(ended['pause_duration']), effective=format_duration(ended['total_duration']))
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.update_service_message(interaction.guild_id)
                await self.bot.send_log(interaction.guild.id, texts['log_stop_title'], texts['log_stop_desc'].format(user=interaction.user.mention), config.COLOR_RED, [("Total", format_duration(total))])
            else: await interaction.followup.send(texts['error_db'], ephemeral=True)
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)