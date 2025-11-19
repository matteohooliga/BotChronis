import os
import sys
import json
import time
import datetime
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from database import ChronosDatabase
from views import ServiceButtonsView

# Charger les variables
load_dotenv()

print("====================================")
print("     CHRONIS BOT - DEMARRAGE")
print("====================================\n")

# ----- Configuration Discord -----
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class ChronosBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )
        self.db = ChronosDatabase()
        self.maintenance_mode = False 

    async def setup_hook(self):
        await self.db.initialize_database()
        await self.load_extension('cogs.commands')
        self.add_view(ServiceButtonsView(self))
        self.scheduled_restart.start()
        print("✅ Tâche de redémarrage automatique planifiée pour 04h00.")

    async def on_ready(self):
        print(f"✅ {self.user} est EN LIGNE et prêt !")
        print(f"ID: {self.user.id}")
        print(f"Serveurs: {len(self.guilds)}")
        
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="les services RP 👮")
        )

        # --- GESTION DE LA MISE À JOUR DES MESSAGES AU DÉMARRAGE ---
        if os.path.exists("restart_context.json"):
            try:
                with open("restart_context.json", "r") as f:
                    data = json.load(f)
                
                # 1. Mise à jour du message de commande (Texte simple)
                if data.get("manual_channel_id") and data.get("manual_message_id"):
                    try:
                        channel = self.get_channel(data["manual_channel_id"]) or await self.fetch_channel(data["manual_channel_id"])
                        msg = await channel.fetch_message(data["manual_message_id"])
                        # On modifie le message texte simple
                        await msg.edit(content="✅ **Redémarrage terminé !** Le bot est de nouveau opérationnel.")
                    except Exception as e:
                        print(f"Impossible de modifier le message de commande : {e}")

                # 2. Mise à jour des messages de logs (Embeds)
                # Gère à la fois le log manuel et les logs de maintenance auto (liste)
                log_messages = data.get("log_messages", [])
                
                for log_info in log_messages:
                    try:
                        c_id = log_info.get("channel_id")
                        m_id = log_info.get("message_id")
                        
                        log_channel = self.get_channel(c_id) or await self.fetch_channel(c_id)
                        log_msg = await log_channel.fetch_message(m_id)
                        
                        # Mise à jour de l'embed de log
                        original_embed = log_msg.embeds[0]
                        new_log_embed = discord.Embed(
                            title=original_embed.title.replace("en cours...", "Terminé") if original_embed.title else "Redémarrage Terminé",
                            description=original_embed.description,
                            color=discord.Color.green()
                        )
                        
                        for field in original_embed.fields:
                            if field.name == "Statut" or field.name == "Durée estimée":
                                new_log_embed.add_field(name="Statut", value="Terminé ✅", inline=True)
                            else:
                                new_log_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                        
                        new_log_embed.set_footer(text=f"Fini le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
                        await log_msg.edit(embed=new_log_embed)
                        
                    except Exception as e:
                        print(f"Erreur update log : {e}")

                # Nettoyage
                os.remove("restart_context.json")

            except Exception as e:
                print(f"Erreur globale lecture restart context : {e}")

    async def on_message(self, message):
        if message.author == self.user: return
        await self.process_commands(message)

    # --- TÂCHE AUTOMATIQUE DE 04H00 ---
    @tasks.loop(time=datetime.time(hour=4, minute=0))
    async def scheduled_restart(self):
        print("⏰ Il est 04h00. Lancement de la maintenance quotidienne...")
        
        # Préparation des données pour le redémarrage
        restart_data = {
            "manual_channel_id": None,
            "manual_message_id": None,
            "log_messages": []
        }

        # Envoi des logs de maintenance sur tous les serveurs
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                if config_data.get('log_channel_id'):
                    try:
                        guild = self.get_guild(int(config_data['guild_id']))
                        log_channel = guild.get_channel(int(config_data['log_channel_id']))
                        if guild and log_channel:
                            embed = discord.Embed(
                                title="🔄 Maintenance Quotidienne",
                                description="Redémarrage automatique pour maintenance.",
                                color=discord.Color.gold()
                            )
                            embed.add_field(name="Durée estimée", value="~5 minutes", inline=True)
                            embed.timestamp = datetime.datetime.now()
                            
                            msg = await log_channel.send(embed=embed)
                            
                            # Sauvegarde pour update au retour
                            restart_data["log_messages"].append({
                                "channel_id": log_channel.id,
                                "message_id": msg.id
                            })
                    except: continue
        except: pass

        # Sauvegarde du contexte
        try:
            with open("restart_context.json", "w") as f:
                json.dump(restart_data, f)
        except: pass

        self.maintenance_mode = True
        await self.close()

    async def update_service_message(self, guild_id: int, config_data: dict = None):
        if not config_data:
            config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data: return

        try:
            guild = self.get_guild(guild_id)
            if not guild: return
            channel = guild.get_channel(int(config_data['channel_id']))
            if not channel: return

            try:
                active_sessions = await self.db.get_all_active_sessions(str(guild_id))
                from utils import create_service_embed
                embed = create_service_embed(active_sessions, guild)
                message = channel.get_partial_message(int(config_data['message_id']))
                await message.edit(embed=embed)
            except: pass
        except Exception as e:
            print(f"Erreur update: {e}")

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERREUR : DISCORD_TOKEN manquant !")
        return

    bot = ChronosBot()

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def sync(ctx):
        print(f"🔄 Sync par {ctx.author}...")
        msg = await ctx.send("⏳ **Sync...**")
        try:
            s = await bot.tree.sync()
            await msg.edit(content=f"✅ **Sync OK !** ({len(s)} commandes)")
        except Exception as e:
            await msg.edit(content=f"❌ Erreur: `{e}`")

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def restart(ctx):
        """Redémarre le bot manuellement"""
        print(f"🔄 Redémarrage demandé par {ctx.author}...")
        
        # 1. Message TEXTE SIMPLE pour la commande
        msg = await ctx.send("👋 **Redémarrage en cours...**")

        # Structure de sauvegarde
        restart_data = {
            "manual_channel_id": ctx.channel.id,
            "manual_message_id": msg.id,
            "log_messages": []
        }

        # 2. Envoi du log (Embed Jaune)
        try:
            config_data = await bot.db.get_guild_config(str(ctx.guild.id))
            if config_data and config_data.get('log_channel_id'):
                log_channel = bot.get_channel(int(config_data['log_channel_id']))
                if log_channel:
                    embed_log = discord.Embed(
                        title="🔄 Redémarrage Manuel",
                        description=f"Déclenché par {ctx.author.mention}.",
                        color=discord.Color.gold()
                    )
                    embed_log.add_field(name="Statut", value="En cours...", inline=True)
                    embed_log.timestamp = datetime.datetime.now()
                    
                    log_msg = await log_channel.send(embed=embed_log)
                    
                    # Ajout à la liste des logs à update
                    restart_data["log_messages"].append({
                        "channel_id": log_channel.id,
                        "message_id": log_msg.id
                    })
        except Exception as e:
            print(f"Erreur log restart : {e}")

        # Sauvegarde du contexte
        try:
            with open("restart_context.json", "w") as f:
                json.dump(restart_data, f)
        except: pass
        
        await bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    try:
        bot.run(token)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt...")
    except Exception as e:
        print(f"❌ Erreur : {e}")

    if bot.maintenance_mode:
        print("🌙 Mode Maintenance. Pause de 5 minutes...")
        time.sleep(300)
        print("🌞 Redémarrage...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()