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
        self._handle_restart_context()

    def _handle_restart_context(self):
        """Gère la mise à jour des messages après un redémarrage"""
        if not os.path.exists("restart_context.json"): return
        
        try:
            with open("restart_context.json", "r") as f:
                data = json.load(f)
            
            # Helper interne pour update un message
            async def update_msg(channel_id, message_id, new_content=None, new_embed=None):
                if not channel_id or not message_id: return
                try:
                    channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                    msg = await channel.fetch_message(message_id)
                    if new_content: await msg.edit(content=new_content)
                    if new_embed: await msg.edit(embed=new_embed)
                except: pass

            # 1. Message de commande
            self.loop.create_task(update_msg(
                data.get("manual_channel_id"), 
                data.get("manual_message_id"), 
                new_content="✅ **Redémarrage terminé !** Le bot est de nouveau opérationnel."
            ))

            # 2. Messages de logs
            for log_info in data.get("log_messages", []):
                async def update_log_embed(c_id, m_id):
                    try:
                        channel = self.get_channel(c_id) or await self.fetch_channel(c_id)
                        msg = await channel.fetch_message(m_id)
                        original = msg.embeds[0]
                        
                        new_embed = discord.Embed(
                            title=original.title.replace("en cours...", "Terminé"),
                            description=original.description,
                            color=discord.Color.green()
                        )
                        for f in original.fields:
                            val = "Terminé ✅" if f.name in ["Statut", "Durée estimée"] else f.value
                            new_embed.add_field(name=f.name, value=val, inline=f.inline)
                        new_embed.set_footer(text=f"Fini le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
                        await msg.edit(embed=new_embed)
                    except: pass
                
                self.loop.create_task(update_log_embed(log_info.get("channel_id"), log_info.get("message_id")))

            # Nettoyage différé pour laisser le temps aux tâches asynchrones
            # os.remove("restart_context.json") # À faire plus proprement dans un vrai contexte, ici simplifié
        except Exception as e:
            print(f"Erreur restart context: {e}")

    async def on_message(self, message):
        if message.author == self.user: return
        await self.process_commands(message)

    # --- SYSTÈME CENTRALISÉ DE LOGS ---
    async def send_log(self, guild_id: int, title: str, description: str, color: discord.Color, fields: list = None):
        """Envoie un log dans le salon configuré du serveur"""
        config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data or not config_data.get('log_channel_id'):
            return

        try:
            log_channel = self.get_channel(int(config_data['log_channel_id']))
            if not log_channel: return

            embed = discord.Embed(title=title, description=description, color=color)
            if fields:
                for name, value in fields:
                    embed.add_field(name=name, value=value, inline=True)
            
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text="Log système Chronis")
            
            return await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Erreur envoi log: {e}")
            return None

    # --- TÂCHE AUTOMATIQUE DE 04H00 ---
    @tasks.loop(time=datetime.time(hour=4, minute=0))
    async def scheduled_restart(self):
        print("⏰ Il est 04h00. Maintenance...")
        restart_data = {"manual_channel_id": None, "manual_message_id": None, "log_messages": []}

        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                if config_data.get('log_channel_id'):
                    try:
                        log_channel = self.get_channel(int(config_data['log_channel_id']))
                        if log_channel:
                            msg = await self.send_log(
                                int(config_data['guild_id']),
                                "🔄 Maintenance Quotidienne",
                                "Redémarrage automatique.",
                                discord.Color.gold(),
                                [("Durée estimée", "~5 minutes")]
                            )
                            if msg:
                                restart_data["log_messages"].append({"channel_id": log_channel.id, "message_id": msg.id})
                    except: continue
        except: pass

        try:
            with open("restart_context.json", "w") as f: json.dump(restart_data, f)
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
        msg = await ctx.send("⏳ **Sync...**")
        try:
            s = await bot.tree.sync()
            await msg.edit(content=f"✅ **Sync OK !** ({len(s)} commandes)")
        except Exception as e:
            await msg.edit(content=f"❌ Erreur: `{e}`")

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def restart(ctx):
        msg = await ctx.send("👋 **Redémarrage en cours...**")
        
        # Log manuel via la nouvelle méthode centralisée
        log_msg = await bot.send_log(
            ctx.guild.id,
            "🔄 Redémarrage Manuel",
            f"Déclenché par {ctx.author.mention}.",
            discord.Color.gold(),
            [("Statut", "En cours...")]
        )

        restart_data = {
            "manual_channel_id": ctx.channel.id,
            "manual_message_id": msg.id,
            "log_messages": []
        }
        if log_msg:
            restart_data["log_messages"].append({"channel_id": log_msg.channel.id, "message_id": log_msg.id})

        try:
            with open("restart_context.json", "w") as f: json.dump(restart_data, f)
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
        print("🌙 Mode Maintenance (5min)...")
        time.sleep(300)
        print("🌞 Redémarrage...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()