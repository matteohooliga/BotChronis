
import discord
from utils import format_duration
import config


class ServiceButtonsView(discord.ui.View):
    """Vue persistante pour les boutons de service"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db

    @discord.ui.button(
        label=config.BUTTONS['start']['label'],
        emoji=config.BUTTONS['start']['emoji'],
        style=discord.ButtonStyle.success,
        custom_id=config.BUTTONS['start']['custom_id']
    )
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Démarrer le service"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Répondre immédiatement pour éviter le timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Vérifier s'il y a déjà une session active
            active_session = self.db.get_active_session(user_id, guild_id)
            
            if active_session:
                await interaction.followup.send(
                    config.MESSAGES['service_already_started'],
                    ephemeral=True
                )
                return
            
            # Démarrer une nouvelle session
            self.db.start_session(user_id, guild_id, interaction.user.display_name)
            
            await interaction.followup.send(
                config.MESSAGES['service_started'],
                ephemeral=True
            )
            
            # Mettre à jour le message principal
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e:
            print(f"Erreur lors du démarrage du service : {e}")
            await interaction.followup.send(
                "❌ Une erreur est survenue lors du démarrage du service.",
                ephemeral=True
            )

    @discord.ui.button(
        label=config.BUTTONS['pause']['label'],
        emoji=config.BUTTONS['pause']['emoji'],
        style=discord.ButtonStyle.primary,
        custom_id=config.BUTTONS['pause']['custom_id']
    )
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mettre en pause ou reprendre le service"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Répondre immédiatement pour éviter le timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Vérifier s'il y a une session active
            active_session = self.db.get_active_session(user_id, guild_id)
            
            if not active_session:
                await interaction.followup.send(
                    config.MESSAGES['service_not_started'],
                    ephemeral=True
                )
                return
            
            # Basculer entre pause et reprise
            if active_session['is_paused']:
                # Reprendre le service
                self.db.resume_session(user_id, guild_id)
                message = config.MESSAGES['service_resumed']
            else:
                # Mettre en pause
                self.db.pause_session(user_id, guild_id)
                message = config.MESSAGES['service_paused']
            
            await interaction.followup.send(message, ephemeral=True)
            
            # Mettre à jour le message principal
            await self.bot.update_service_message(interaction.guild_id)
        except Exception as e:
            print(f"Erreur lors de la pause/reprise du service : {e}")
            await interaction.followup.send(
                "❌ Une erreur est survenue.",
                ephemeral=True
            )

    @discord.ui.button(
        label=config.BUTTONS['stop']['label'],
        emoji=config.BUTTONS['stop']['emoji'],
        style=discord.ButtonStyle.danger,
        custom_id=config.BUTTONS['stop']['custom_id']
    )
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Terminer le service"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Répondre immédiatement pour éviter le timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Vérifier s'il y a une session active
            active_session = self.db.get_active_session(user_id, guild_id)
            
            if not active_session:
                await interaction.followup.send(
                    config.MESSAGES['service_not_started'],
                    ephemeral=True
                )
                return
            
            # Terminer la session
            ended_session = self.db.end_session(user_id, guild_id)
            
            if ended_session:
                # Calculer les durées
                total_duration = format_duration(ended_session['total_duration'])
                pause_duration = format_duration(ended_session['pause_duration'])
                effective_duration = format_duration(
                    ended_session['total_duration']
                )
                
                message = config.MESSAGES['service_stopped'].format(
                    duration=total_duration,
                    pause=pause_duration,
                    effective=effective_duration
                )
                
                await interaction.followup.send(message, ephemeral=True)
                
                # Mettre à jour le message principal
                await self.bot.update_service_message(interaction.guild_id)
            else:
                await interaction.followup.send(
                    "❌ Erreur lors de la fermeture du service.",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Erreur lors de l'arrêt du service : {e}")
            await interaction.followup.send(
                "❌ Une erreur est survenue lors de l'arrêt du service.",
                ephemeral=True
            )
