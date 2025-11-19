import discord
import config
import json
from utils import format_duration, check_permissions

class ServiceButtonsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db

    async def _check_access(self, interaction: discord.Interaction) -> bool:
        config_data = await self.db.get_guild_config(str(interaction.guild_id))
        allowed_roles = None
        if config_data and config_data['allowed_roles']:
            try:
                allowed_roles = json.loads(config_data['allowed_roles'])
            except: pass
        
        if not check_permissions(interaction.user, allowed_roles):
            await interaction.response.send_message("⛔ Permission refusée.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label=config.BUTTONS['start']['label'], emoji=config.BUTTONS['start']['emoji'], style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        try:
            if await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                await interaction.followup.send(config.MESSAGES['service_already_started'], ephemeral=True)
                return
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await interaction.followup.send(config.MESSAGES['service_started'], ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e:
            await interaction.followup.send("❌ Erreur.", ephemeral=True)

    @discord.ui.button(label=config.BUTTONS['pause']['label'], emoji=config.BUTTONS['pause']['emoji'], style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        try:
            active_session = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not active_session:
                await interaction.followup.send(config.MESSAGES['service_not_started'], ephemeral=True)
                return
            
            if active_session['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                msg = config.MESSAGES['service_resumed']
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                msg = config.MESSAGES['service_paused']
            await interaction.followup.send(msg, ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e:
            await interaction.followup.send("❌ Erreur.", ephemeral=True)

    @discord.ui.button(label=config.BUTTONS['stop']['label'], emoji=config.BUTTONS['stop']['emoji'], style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                await interaction.followup.send(config.MESSAGES['service_not_started'], ephemeral=True)
                return
            
            ended = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if ended:
                # Calcul corrigé : Total = Effectif + Pause
                effective = ended['total_duration']
                pause = ended['pause_duration']
                real_total = effective + pause
                
                msg = config.MESSAGES['service_stopped'].format(
                    duration=format_duration(real_total),
                    pause=format_duration(pause),
                    effective=format_duration(effective)
                )
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.update_service_message(interaction.guild_id)
            else:
                await interaction.followup.send("❌ Erreur fermeture.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ Erreur.", ephemeral=True)