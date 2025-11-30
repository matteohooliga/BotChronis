import os
import sys
import json
import time
import datetime
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Imports locaux
from database import ChronosDatabase
# MODIF ICI : AJOUT DE AbsenceView
from views import ServiceButtonsView, RdvPatientView, RdvStaffView, RdvTicketView, AbsenceView
from utils import format_duration, create_service_embed
import config

# Chargement des variables d'environnement (.env)
load_dotenv()

print("====================================")
print("     CHRONIS BOT - DEMARRAGE")
print("====================================\n")

# Configuration des Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class ChronosBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="+", intents=intents, help_command=None)
        self.db = ChronosDatabase()
        self.maintenance_mode = False 

    async def setup_hook(self):
        # 1. Initialisation de la Base de Données
        await self.db.initialize_database()
        
        # 2. Chargement de l'extension
        try:
            await self.load_extension('cogs.commands')
            print("✅ Extension 'cogs.commands' chargée avec succès.")
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE lors du chargement de 'cogs.commands':\n{e}")
            
        # 3. Ajout de la vue persistante GLOBAL
        self.add_view(ServiceButtonsView(self))
        self.add_view(RdvStaffView(self))
        self.add_view(RdvTicketView(self))
        self.add_view(AbsenceView(self)) # AJOUT DE LA VUE PERSISTANTE ABSENCE
        
        # 4. RESTAURATION DES PANNEAUX RDV
        print("🔄 Restauration des panneaux RDV...")
        try:
            configs = await self.db.get_all_guild_configs()
            count = 0
            for config_data in configs:
                if config_data.get('rdv_message_id') and config_data.get('rdv_types'):
                    try:
                        rdv_types = json.loads(config_data['rdv_types'])
                        message_id = int(config_data['rdv_message_id'])
                        lang = config_data.get('language', 'fr')
                        view = RdvPatientView(self, rdv_types, lang)
                        self.add_view(view, message_id=message_id)
                        count += 1
                    except Exception as e:
                        print(f"⚠️ Erreur restauration RDV pour guilde {config_data.get('guild_id')}: {e}")
            print(f"✅ {count} panneaux RDV restaurés avec succès.")
        except Exception as e:
            print(f"❌ Erreur générale restauration RDV: {e}")

        # 5. Lancement des tâches de fond
        self.scheduled_restart.start()
        self.status_task.start()
        
        print("✅ Tâches automatiques démarrées.")
        print("✅ Setup terminé. Le bot est prêt.")

    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user} (ID: {self.user.id})")
        await self.update_status()
        await self._handle_restart_context()

    async def on_guild_join(self, guild):
        txt = config.TRANSLATIONS['fr']
        await self.send_system_log(
            txt['log_guild_join_title'], 
            txt['log_guild_join_desc'], 
            discord.Color.green(),
            [
                (txt['log_guild_join_name'], guild.name),
                (txt['log_guild_join_id'], str(guild.id)),
                (txt['log_guild_join_owner'], str(guild.owner)),
                (txt['log_guild_join_members'], str(guild.member_count))
            ]
        )

    # --- UTILITAIRES ---

    async def get_guild_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        return data['language'] if data and data.get('language') else 'fr'

    async def send_log(self, guild_id: int, title: str, description: str, color: discord.Color, fields: list = None):
        config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data or not config_data.get('log_channel_id'): return
            
        try:
            log_channel = self.get_channel(int(config_data['log_channel_id']))
            if not log_channel: return
            embed = discord.Embed(title=title, description=description, color=color)
            if fields:
                for name, value in fields:
                    embed.add_field(name=name, value=value, inline=True)
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text="Chronis Logs")
            return await log_channel.send(embed=embed)
        except: return None
    
    async def send_system_log(self, title: str, description: str, color: discord.Color, fields: list = None):
        if not config.DEV_LOG_CHANNEL_ID: return None
        target_id = config.DEV_LOG_CHANNEL_ID
        channel = self.get_channel(target_id)
        if not channel:
            try: channel = await self.fetch_channel(target_id)
            except: return None
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now())
        if fields:
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=True)
        embed.set_footer(text="Chronis System")
        return await channel.send(embed=embed)

    # --- OPTIMISATION ICI : Ajout du param active_sessions ---
    async def update_service_message(self, guild_id: int, config_data: dict = None, active_sessions: list = None):
        if not config_data:
            config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data: return
            
        try:
            channel = self.get_channel(int(config_data['channel_id']))
            if not channel: return
            
            # Si on a déjà les sessions (via commands.py), on les utilise, sinon on requête
            active = active_sessions if active_sessions is not None else await self.db.get_all_active_sessions(str(guild_id))
            
            is_maint = int(config_data.get('is_maintenance', 0)) == 1
            lang = config_data.get('language', 'fr')
            
            embed = create_service_embed(active, channel.guild, lang, is_maint)
            try:
                message = channel.get_partial_message(int(config_data['message_id']))
                await message.edit(embed=embed)
            except discord.NotFound: pass
        except: pass

    # --- TÂCHES DE FOND ---

    @tasks.loop(seconds=30)
    async def status_task(self):
        await self.update_status()

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    async def update_status(self):
        try:
            if self.maintenance_mode:
                await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Maintenance en cours"))
            else:
                total = await self.db.get_total_active_sessions_count()
                ping = round(self.latency * 1000)
                status_text = f"{total} agents actifs | {ping}ms | /about"
                await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
        except: pass

    @tasks.loop(time=datetime.time(hour=3, minute=0))
    async def scheduled_restart(self):
        print("⏰ 04h00 (Heure Locale) : Maintenance automatique...")
        restart_data = {"manual_channel_id": None, "manual_message_id": None, "log_messages": []}
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                guild_id = int(config_data['guild_id'])
                active = await self.db.get_all_active_sessions(str(guild_id))
                if active:
                    for s in active:
                        await self.db.end_session(s['user_id'], str(guild_id))
                    await self.update_service_message(guild_id, config_data)
            txt = config.TRANSLATIONS['fr']
            msg = await self.send_system_log(txt['log_maint_title'], txt['log_maint_desc'], discord.Color.gold(), [(txt['log_stat_wip'], "~5 minutes")])
            if msg:
                restart_data["log_messages"].append({"channel_id": msg.channel.id, "message_id": msg.id})
        except: pass
        
        try:
            with open("restart_context.json", "w") as f:
                json.dump(restart_data, f)
        except: pass
            
        self.maintenance_mode = True
        await self.update_status()
        await self.close()

    async def _handle_restart_context(self):
        if not os.path.exists("restart_context.json"): return
        try:
            with open("restart_context.json", "r") as f:
                data = json.load(f)
            
            if data.get("manual_channel_id") and data.get("manual_message_id"):
                try:
                    channel = self.get_channel(data["manual_channel_id"]) or await self.fetch_channel(data["manual_channel_id"])
                    msg = await channel.fetch_message(data["manual_message_id"])
                    lang = await self.get_guild_lang(channel.guild.id)
                    txt = config.TRANSLATIONS[lang]
                    await msg.edit(content=txt['cmd_restart_end'])
                except: pass

            for log_info in data.get("log_messages", []):
                try:
                    c_id = log_info.get("channel_id")
                    m_id = log_info.get("message_id")
                    channel = self.get_channel(c_id) or await self.fetch_channel(c_id)
                    msg = await channel.fetch_message(m_id)
                    lang = await self.get_guild_lang(channel.guild.id)
                    txt = config.TRANSLATIONS[lang]

                    original = msg.embeds[0]
                    new_title = original.title
                    if "Mainten" in str(original.title): new_title = txt['log_maint_title']
                    elif "Start" in str(original.title) or "Manuel" in str(original.title): new_title = txt['log_restart_title']
                    
                    new_embed = discord.Embed(title=new_title, description=original.description, color=discord.Color.green())
                    date_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                    new_embed.set_footer(text=txt['log_footer_done'].format(date=date_str))
                    
                    await msg.edit(embed=new_embed)
                except: pass
            os.remove("restart_context.json") 
        except Exception as e:
            print(f"Erreur restart context: {e}")

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERREUR : Le token DISCORD_TOKEN est manquant dans le fichier .env")
        return

    bot = ChronosBot()

    @bot.check
    async def globally_block_blacklisted(ctx):
        if await bot.db.is_blacklisted(str(ctx.author.id)): return False
        return True

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def sync(ctx):
        msg = await ctx.send("⏳ **Synchronisation en cours...**")
        try:
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ **{len(synced)} commandes synchronisées !**")
        except Exception as e:
            await msg.edit(content=f"❌ Erreur lors de la synchro : `{e}`")

    @bot.command()
    @commands.is_owner()
    async def sync_global(ctx):
        msg = await ctx.send("🌍 **Synchronisation Globale en cours...** (Cela peut prendre jusqu'à 1h)")
        try:
            # On sync sans préciser de "guild", donc c'est pour tout Discord
            synced = await bot.tree.sync()
            await msg.edit(content=f"✅ **{len(synced)} commandes synchronisées globalement !**\n(Redémarre ton Discord avec CTRL+R si tu ne les vois pas)")
        except Exception as e:
            await msg.edit(content=f"❌ Erreur : `{e}`")

    @bot.command()
    @commands.is_owner()
    async def fix_doublons(ctx):
        msg = await ctx.send("🧹 **Nettoyage violent des doublons...**")
        try:
            bot.tree.clear_commands(guild=ctx.guild)
            await bot.tree.sync(guild=ctx.guild)
            
            synced = await bot.tree.sync()
            
            await msg.edit(content=f"✅ **Nettoyage terminé !**\nJ'ai supprimé les commandes locales et rechargé les {len(synced)} commandes globales.\n\n👉 **IMPORTANT : Fais CTRL + R maintenant pour voir le résultat.**")
        except Exception as e:
            await msg.edit(content=f"❌ Erreur : `{e}`")

    @bot.command()
    @commands.is_owner()
    async def debug(ctx):
        msg = await ctx.send("🔄 **Rechargement de l'extension...**")
        try:
            await bot.reload_extension('cogs.commands')
            await msg.edit(content="✅ **Extension rechargée avec succès !**")
        except Exception as e:
            await msg.edit(content=f"❌ **ERREUR CRITIQUE** :\n```py\n{e}\n```")

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def restart(ctx):
        import config as cfg
        lang = await bot.get_guild_lang(ctx.guild.id)
        txt = cfg.TRANSLATIONS[lang]
        msg = await ctx.send(txt['cmd_restart_start'])
        restart_data = {"manual_channel_id": ctx.channel.id, "manual_message_id": msg.id, "log_messages": []}
        user_display = f"{ctx.author.name} ({ctx.author.id})"
        log_msg = await bot.send_system_log(
            txt['log_restart_title'], 
            txt['log_restart_desc'].format(user=user_display), 
            discord.Color.gold(), 
            [("Status", txt['log_stat_wip'])]
        )
        if log_msg:
            restart_data["log_messages"].append({"channel_id": log_msg.channel.id, "message_id": log_msg.id})
        try:
            with open("restart_context.json", "w") as f: json.dump(restart_data, f)
        except: pass
        await bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @bot.command()
    @commands.is_owner()
    async def maintenance(ctx, state: str = None):
        if state not in ["on", "off"]: return await ctx.send("Usage: `+maintenance on` ou `off`")
        new_val = 1 if state == "on" else 0
        bot.maintenance_mode = (new_val == 1)
        await bot.update_status()
        await bot.db.set_global_maintenance(new_val)
        configs = await bot.db.get_all_guild_configs()
        count = 0
        for c in configs:
            c['is_maintenance'] = new_val 
            await bot.update_service_message(int(c['guild_id']), c)
            count += 1
        msg = "Maintenance ACTIVÉE" if new_val else "Maintenance DÉSACTIVÉE"
        await ctx.send(f"✅ {msg} sur {count} serveurs.")

    @bot.command()
    @commands.is_owner()
    async def stop(ctx):
        await ctx.send("🛑 Arrêt du bot.")
        await bot.close()
        sys.exit(0)
        
    @bot.command()
    @commands.is_owner()
    async def start(ctx):
        await ctx.send("🟢 Bot en ligne.")

    @bot.command()
    @commands.is_owner()
    async def infos(ctx):
        guild_count = len(bot.guilds)
        lines = []
        for g in bot.guilds[:15]:
            lines.append(f"• **{g.name}** (`{g.id}`)\n  👑 {g.owner} | 👥 {g.member_count}")
        desc = "\n".join(lines)
        if len(bot.guilds) > 15: desc += f"\n\n... et {len(bot.guilds)-15} autres."
        embed = discord.Embed(title="📊 Infos Serveurs", description=f"Total : **{guild_count}** serveurs", color=config.BOT_COLOR)
        embed.add_field(name="Liste", value=desc or "Aucun", inline=False)
        await ctx.send(embed=embed)

    try:
        bot.run(token)
    except KeyboardInterrupt:
        pass
    
    if bot.maintenance_mode:
        time.sleep(300)
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()