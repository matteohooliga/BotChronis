import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from typing import List
from datetime import datetime
from utils import create_stats_embed, create_all_stats_embed, create_service_embed, format_duration
import config

class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.refresh_service.start()

    def cog_unload(self):
        self.refresh_service.cancel()

    # --- BOUCLE DE RAFRAÎCHISSEMENT (10 secondes) ---
    # Modification ici : 1s -> 10s pour éviter l'erreur 429 (Rate Limit)
    @tasks.loop(seconds=10)
    async def refresh_service(self):
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                try:
                    guild_id = int(config_data['guild_id'])
                    # On ne refresh que s'il y a des gens en service pour économiser l'API
                    active_sessions = await self.db.get_all_active_sessions(str(guild_id))
                    if not active_sessions:
                        continue
                    await self.bot.update_service_message(guild_id, config_data)
                except Exception:
                    continue
        except Exception as e:
            print(f"Erreur boucle refresh : {e}")

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

    @app_commands.command(name="about", description="Afficher les informations et liens du bot")
    async def about_command(self, interaction: discord.Interaction):
        """Affiche les crédits, le support et le lien GitHub"""
        embed = discord.Embed(
            title=f"ℹ️ À propos de {config.BOT_NAME}",
            description="Chronis est un bot de gestion de temps de service conçu pour faciliter la vie des serveurs Roleplay.",
            color=config.BOT_COLOR
        )
        
        embed.add_field(name="📦 Version", value=f"`{config.BOT_VERSION}`", inline=True)
        embed.add_field(name="💻 Développeur", value=f"matteohooliga\n`({config.OWNER_ID})`", inline=True)
        embed.add_field(name="🟢 Latence", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        
        links_value = f"• [📂 **Code Source (GitHub)**]({config.GITHUB_LINK})\n"
        if "discord.gg" in config.SUPPORT_LINK:
             links_value += f"• [🆘 **Serveur de Support**]({config.SUPPORT_LINK})"
        
        embed.add_field(name="🔗 Liens Utiles", value=links_value, inline=False)
        
        embed.set_footer(text=f"Développé avec ❤️ par matteohooliga")
        embed.timestamp = datetime.now()
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Code Source", url=config.GITHUB_LINK, style=discord.ButtonStyle.url))
        if "discord.gg" in config.SUPPORT_LINK:
            view.add_item(discord.ui.Button(label="Support Discord", url=config.SUPPORT_LINK, style=discord.ButtonStyle.url))
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="sum", description="Afficher vos statistiques de service")
    async def sum_command(self, interaction: discord.Interaction, user: discord.User = None):
        target_user = user or interaction.user
        stats = await self.db.get_user_stats(str(target_user.id), str(interaction.guild_id))
        embed = create_stats_embed(stats, target_user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sumall", description="Afficher les statistiques globales")
    async def sumall_command(self, interaction: discord.Interaction):
        all_stats = await self.db.get_all_users_stats(str(interaction.guild_id))
        embed = create_all_stats_embed(all_stats, interaction.guild)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="close", description="Forcer la fermeture d'une session active")
    @app_commands.autocomplete(user_id=close_user_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def close_command(self, interaction: discord.Interaction, user_id: str):
        session = await self.db.get_active_session(str(user_id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(config.MESSAGES['no_active_session'], ephemeral=True)
        
        try:
            user_obj = interaction.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            user_mention = user_obj.mention
        except: user_mention = f"<@{user_id}>"

        ended = await self.db.end_session(str(user_id), str(interaction.guild_id))
        if ended:
            duration = format_duration(ended['total_duration'])
            msg = config.MESSAGES['service_forced_stop'].format(user=user_mention, duration=duration)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            
            await self.bot.send_log(
                interaction.guild.id,
                "🔧 Service Fermé (Force Close)",
                "Une session a été fermée manuellement.",
                discord.Color.orange(),
                [("Cible", user_mention), ("Modérateur", interaction.user.mention), ("Durée validée", f"`{duration}`")]
            )
        else: await interaction.response.send_message("❌ Erreur.", ephemeral=True)

    @app_commands.command(name="edittime", description="Modifier le temps de service d'un joueur")
    @app_commands.choices(operation=[app_commands.Choice(name="Ajouter (+)", value="add"), app_commands.Choice(name="Retirer (-)", value="remove")])
    @app_commands.default_permissions(manage_guild=True)
    async def edittime_command(self, interaction: discord.Interaction, user: discord.User, operation: app_commands.Choice[str], minutes: int):
        if minutes <= 0: return await interaction.response.send_message("⚠️ Minutes > 0 requises.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        
        ms = minutes * 60 * 1000 * (1 if operation.value == "add" else -1)
        try:
            await self.db.add_time_adjustment(str(user.id), str(interaction.guild_id), user.display_name, ms)
            action = "ajouté" if operation.value == "add" else "retiré"
            await interaction.followup.send(f"✅ {action.capitalize()} **{minutes} min** à {user.mention}.", ephemeral=True)
            
            await self.bot.send_log(
                interaction.guild.id,
                "📈 Temps Modifié",
                "Modification manuelle du temps de service.",
                discord.Color.blue(),
                [("Modérateur", interaction.user.mention), ("Cible", user.mention), ("Action", action), ("Valeur", f"{minutes} min")]
            )
        except Exception as e: await interaction.followup.send(f"❌ Erreur: `{e}`", ephemeral=True)

    @app_commands.command(name="reset", description="Réinitialiser les données (ADMIN)")
    @app_commands.default_permissions(administrator=True)
    async def reset_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            n = await self.db.reset_guild_stats(str(interaction.guild_id))
            await interaction.followup.send(f"🧹 Reset effectué. {n} sessions supprimées.", ephemeral=True)
            await self.bot.update_service_message(interaction.guild_id)
            
            await self.bot.send_log(
                interaction.guild.id,
                "⚠️ Réinitialisation Totale",
                "Toutes les données de service ont été supprimées.",
                discord.Color.red(),
                [("Admin", interaction.user.mention), ("Sessions supprimées", str(n))]
            )
        except Exception as e: await interaction.followup.send(f"❌ Erreur: `{e}`", ephemeral=True)

    @app_commands.command(name="setup", description="Configurer le système")
    @app_commands.default_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel, log_channel: discord.abc.GuildChannel = None):
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Le salon de service doit être un salon textuel.", ephemeral=True)
        if log_channel and not isinstance(log_channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Le salon de logs doit être un salon textuel.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            from views import ServiceButtonsView
            from utils import create_service_embed
            embed = create_service_embed([], interaction.guild)
            view = ServiceButtonsView(self.bot)
            msg = await channel.send(embed=embed, view=view)
            await self.db.set_guild_config(str(interaction.guild_id), str(channel.id), str(msg.id), str(log_channel.id) if log_channel else None)
            await interaction.followup.send(f"✅ Configuré dans {channel.mention}" + (f" (Logs: {log_channel.mention})" if log_channel else ""), ephemeral=True)
        except Exception as e: await interaction.followup.send(f"❌ Erreur: ```{e}```", ephemeral=True)

    @app_commands.command(name="cancel", description="Annuler session")
    async def cancel_command(self, interaction: discord.Interaction):
        session = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
        if not session: return await interaction.response.send_message(config.MESSAGES['service_not_started'], ephemeral=True)
        
        async with aiosqlite.connect(self.db.db_name) as db:
            await db.execute("DELETE FROM sessions WHERE id = ?", (session['id'],))
            await db.commit()
        
        await interaction.response.send_message("🗑️ Session annulée.", ephemeral=True)
        await self.bot.update_service_message(interaction.guild_id)
        
        await self.bot.send_log(
            interaction.guild.id,
            "🗑️ Service Annulé",
            "Un utilisateur a annulé sa session (données supprimées).",
            discord.Color.dark_red(),
            [("Utilisateur", interaction.user.mention)]
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ServiceCommands(bot))