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
            try: allowed_roles = json.loads(config_data['allowed_roles'])
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
                return await interaction.followup.send(config.MESSAGES['service_already_started'], ephemeral=True)
            
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await interaction.followup.send(config.MESSAGES['service_started'], ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            
            # LOG DÉBUT SERVICE
            await self.bot.send_log(
                interaction.guild_id,
                "🟢 Prise de Service",
                f"{interaction.user.mention} a commencé son service.",
                discord.Color.green()
            )

        except Exception as e: await interaction.followup.send("❌ Erreur.", ephemeral=True)

    @discord.ui.button(label=config.BUTTONS['pause']['label'], emoji=config.BUTTONS['pause']['emoji'], style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        try:
            active_session = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not active_session: return await interaction.followup.send(config.MESSAGES['service_not_started'], ephemeral=True)
            
            if active_session['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(config.MESSAGES['service_resumed'], ephemeral=True)
                
                # LOG REPRISE
                await self.bot.send_log(
                    interaction.guild_id,
                    "▶️ Reprise de Service",
                    f"{interaction.user.mention} a repris son service.",
                    discord.Color.blue() # Bleu pour reprise
                )
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(config.MESSAGES['service_paused'], ephemeral=True)
                
                # LOG PAUSE
                await self.bot.send_log(
                    interaction.guild_id,
                    "⏸️ Pause de Service",
                    f"{interaction.user.mention} s'est mis en pause.",
                    discord.Color.gold() # Orange/Jaune pour pause
                )
            
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e: await interaction.followup.send("❌ Erreur.", ephemeral=True)

    @discord.ui.button(label=config.BUTTONS['stop']['label'], emoji=config.BUTTONS['stop']['emoji'], style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)):
                return await interaction.followup.send(config.MESSAGES['service_not_started'], ephemeral=True)
            
            ended = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if ended:
                effective = ended['total_duration']
                pause = ended['pause_duration']
                real_total = effective + pause
                
                # Formatage pour le message utilisateur
                msg = config.MESSAGES['service_stopped'].format(
                    duration=format_duration(real_total),
                    pause=format_duration(pause),
                    effective=format_duration(effective)
                )
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.update_service_message(interaction.guild_id)

                # LOG FIN SERVICE
                await self.bot.send_log(
                    interaction.guild_id,
                    "🛑 Fin de Service",
                    f"{interaction.user.mention} a terminé son service.",
                    discord.Color.red(),
                    fields=[
                        ("Temps Total", format_duration(real_total)),
                        ("Pauses", format_duration(pause)),
                        ("Temps Effectif", format_duration(effective))
                    ]
                )
            else: await interaction.followup.send("❌ Erreur fermeture.", ephemeral=True)
        except Exception as e: await interaction.followup.send("❌ Erreur.", ephemeral=True)