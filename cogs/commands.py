
import discord
from discord import app_commands
from discord.ext import commands
from database import ChronosDatabase
from utils import (
    create_stats_embed,
    create_all_stats_embed,
    create_service_embed,
    format_duration
)
import config


class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = ChronosDatabase()

    @app_commands.command(name="sum", description="Afficher vos statistiques de service")
    @app_commands.describe(user="L'utilisateur dont vous voulez voir les statistiques (optionnel)")
    async def sum_command(
        self, 
        interaction: discord.Interaction, 
        user: discord.User = None
    ):
        """Afficher les statistiques d'un utilisateur"""
        target_user = user or interaction.user
        
        # Récupérer les stats
        stats = self.db.get_user_stats(str(target_user.id), str(interaction.guild_id))
        
        # Créer l'embed
        embed = create_stats_embed(stats, target_user)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sumall", description="Afficher les statistiques de tous les utilisateurs")
    async def sumall_command(self, interaction: discord.Interaction):
        """Afficher les statistiques globales"""
        # Récupérer toutes les stats
        all_stats = self.db.get_all_users_stats(str(interaction.guild_id))
        
        # Créer l'embed
        embed = create_all_stats_embed(all_stats, interaction.guild)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="close", description="Forcer la fermeture d'une session de service")
    @app_commands.describe(user="L'utilisateur dont la session doit être fermée")
    @app_commands.default_permissions(manage_guild=True)
    async def close_command(
        self, 
        interaction: discord.Interaction, 
        user: discord.User
    ):
        """Forcer la fermeture d'une session (admin seulement)"""
        # Vérifier si l'utilisateur a une session active
        session = self.db.get_active_session(str(user.id), str(interaction.guild_id))
        
        if not session:
            await interaction.response.send_message(
                config.MESSAGES['no_active_session'],
                ephemeral=True
            )
            return
        
        # Terminer la session
        ended_session = self.db.end_session(str(user.id), str(interaction.guild_id))
        
        if ended_session:
            duration = format_duration(ended_session['total_duration'])
            message = config.MESSAGES['service_forced_stop'].format(
                user=user.mention,
                duration=duration
            )
            
            await interaction.response.send_message(message)
            
            # Mettre à jour le message de service
            await self.update_service_message(interaction.guild)

    @app_commands.command(name="reset", description="Réinitialiser toutes les heures de service du serveur (ADMIN)")
    @app_commands.default_permissions(administrator=True)
    async def reset_command(self, interaction: discord.Interaction):
        """Supprime toutes les sessions du serveur courant"""
        await interaction.response.defer(ephemeral=True)

        try:
            deleted = self.db.reset_guild_stats(str(interaction.guild_id))
            await interaction.followup.send(
                f"🧹 **Réinitialisation effectuée**.\n{deleted} session(s) supprimée(s) pour ce serveur.",
                ephemeral=True
            )

            # Mettre à jour le message principal
            await self.update_service_message(interaction.guild)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erreur lors de la réinitialisation : `{e}`",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Erreur lors de la fermeture de la session.",
                ephemeral=True
            )

    @app_commands.command(name="setup", description="Configurer le système de service sur ce serveur")
    @app_commands.describe(channel="Le salon où afficher le système de service")
    @app_commands.default_permissions(administrator=True)
    async def setup_command(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel = None
    ):
        """Configurer le bot sur le serveur"""
        target_channel = channel or interaction.channel
        
        # Vérifier les permissions
        permissions = target_channel.permissions_for(interaction.guild.me)
        if not (permissions.send_messages and permissions.embed_links and permissions.read_message_history):
            await interaction.response.send_message(
                "❌ Le bot n'a pas les permissions nécessaires dans ce salon.\n"
                "Permissions requises : `Envoyer des messages`, `Intégrer des liens`, `Lire l'historique des messages`",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Importer ServiceButtonsView
            from views import ServiceButtonsView
            
            # Créer l'embed et les boutons
            embed = create_service_embed([], interaction.guild)
            view = ServiceButtonsView(self.bot)
            
            # Envoyer le message
            message = await target_channel.send(embed=embed, view=view)
            
            # Sauvegarder la configuration
            self.db.set_guild_config(
                str(interaction.guild_id),
                str(target_channel.id),
                str(message.id)
            )
            
            await interaction.followup.send(
                config.MESSAGES['setup_complete'].format(channel=target_channel.mention),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"{config.MESSAGES['setup_error']}\n```{str(e)}```",
                ephemeral=True
            )

    @app_commands.command(name="cancel", description="Annuler votre session actuelle sans l'enregistrer")
    async def cancel_command(self, interaction: discord.Interaction):
        """Annuler la session en cours"""
        session = self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
        
        if not session:
            await interaction.response.send_message(
                config.MESSAGES['service_not_started'],
                ephemeral=True
            )
            return
        
        # Supprimer directement la session de la base de données
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session['id'],))
        conn.commit()
        
        await interaction.response.send_message(
            "🗑️ **Session annulée** !\nVotre session a été supprimée sans être enregistrée.",
            ephemeral=True
        )
        
        # Mettre à jour le message de service
        await self.update_service_message(interaction.guild)

    async def update_service_message(self, guild: discord.Guild):
        """Mettre à jour le message de service principal"""
        config_data = self.db.get_guild_config(str(guild.id))
        
        if not config_data:
            return
        
        try:
            channel = guild.get_channel(int(config_data['channel_id']))
            if not channel:
                return
            
            message = await channel.fetch_message(int(config_data['message_id']))
            if not message:
                return
            
            # Récupérer les sessions actives
            active_sessions = self.db.get_all_active_sessions(str(guild.id))
            
            # Créer le nouvel embed (garder la view existante avec les callbacks)
            embed = create_service_embed(active_sessions, guild)
            
            await message.edit(embed=embed)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du message de service : {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))
