import discord
import config
import json
from utils import format_duration, check_permissions

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

    async def _check_access(self, interaction: discord.Interaction) -> bool:
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        allowed = json.loads(config_data['allowed_roles']) if config_data and config_data.get('allowed_roles') else None
        if not check_permissions(interaction.user, allowed):
            await interaction.response.send_message("⛔ Permission denied.", ephemeral=True)
            return False
        return True

    async def get_txt(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        lang = data['language'] if data and data.get('language') else 'fr'
        return config.TRANSLATIONS[lang]

    @discord.ui.button(label="Start", emoji=config.BUTTONS['start']['emoji'], style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        txt = await self.get_txt(interaction.guild_id)
        try:
            if await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                return await interaction.followup.send(txt['service_already_started'], ephemeral=True)
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await interaction.followup.send(txt['service_started'], ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            await self.bot.send_log(interaction.guild.id, "🟢 Service", f"{interaction.user.mention} start.", discord.Color.green())
        except: await interaction.followup.send("❌ Error.", ephemeral=True)

    @discord.ui.button(label="Pause", emoji=config.BUTTONS['pause']['emoji'], style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        txt = await self.get_txt(interaction.guild_id)
        try:
            active = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not active: return await interaction.followup.send(txt['service_not_started'], ephemeral=True)
            if active['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(txt['service_resumed'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, "▶️ Resume", f"{interaction.user.mention} resume.", discord.Color.blue())
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(txt['service_paused'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, "⏸️ Pause", f"{interaction.user.mention} pause.", discord.Color.gold())
            await self.bot.update_service_message(interaction.guild_id)
        except: await interaction.followup.send("❌ Error.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji=config.BUTTONS['stop']['emoji'], style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        txt = await self.get_txt(interaction.guild_id)
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                return await interaction.followup.send(txt['service_not_started'], ephemeral=True)
            ended = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if ended:
                total = ended['total_duration'] + ended['pause_duration']
                msg = txt['service_stopped'].format(duration=format_duration(total), pause=format_duration(ended['pause_duration']), effective=format_duration(ended['total_duration']))
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.update_service_message(interaction.guild_id)
                await self.bot.send_log(interaction.guild.id, "🛑 Stop", f"{interaction.user.mention} stop.", discord.Color.red(), [("Total", format_duration(total))])
            else: await interaction.followup.send("❌ Error.", ephemeral=True)
        except: await interaction.followup.send("❌ Error.", ephemeral=True)