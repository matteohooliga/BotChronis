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
from utils import format_duration
import config

# Charger les variables
load_dotenv()

print("====================================")
print("     CHRONIS BOT - DEMARRAGE")
print("====================================\n")

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
        await self.db.initialize_database()
        await self.load_extension('cogs.commands')
        self.add_view(ServiceButtonsView(self))
        self.scheduled_restart.start()
        self.status_task.start()
        print("✅ Tâches automatiques démarrées.")
        print("✅ Setup terminé. Utilisez +sync pour synchroniser les commandes.")

    async def on_ready(self):
        print(f"✅ {self.user} est EN LIGNE et prêt !")
        await self.update_status()
        await self._handle_restart_context()

    # --- EVENT: Ajout du bot à un serveur ---
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

    async def get_guild_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id))
        return data['language'] if data and data.get('language') else 'fr'

    async def _handle_restart_context(self):
        if not os.path.exists("restart_context.json"): return
        try:
            with open("restart_context.json", "r") as f:
                data = json.load(f)
            
            async def update_msg(channel_id, message_id, new_content=None, new_embed=None):
                if not channel_id or not message_id: return
                try:
                    channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                    msg = await channel.fetch_message(message_id)
                    if new_content: await msg.edit(content=new_content)
                    if new_embed: await msg.edit(embed=new_embed)
                except: pass

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
                    elif "Start" in str(original.title) or "Manuel" in str(original.title) or "Manual" in str(original.title): new_title = txt['log_restart_title']
                    
                    new_embed = discord.Embed(title=new_title, description=original.description, color=discord.Color.green())
                    for f in original.fields:
                        val = txt['log_stat_done'] if f.name in ["Statut", "Status", "Durée estimée", "Estimated duration"] else f.value
                        new_embed.add_field(name=f.name, value=val, inline=f.inline)
                    
                    date_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                    new_embed.set_footer(text=txt['log_footer_done'].format(date=date_str))
                    await msg.edit(embed=new_embed)
                except: pass
            os.remove("restart_context.json") 
        except Exception as e: print(f"Erreur restart context: {e}")

    async def on_message(self, message):
        if message.author == self.user: return
        await self.process_commands(message)

    async def update_status(self):
        try:
            if self.maintenance_mode:
                txt = config.TRANSLATIONS['fr']['maint_block_msg']
                await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Maintenance"))
            else:
                total = await self.db.get_total_active_sessions_count()
                ping = round(self.latency * 1000)
                status_text = f"{total} active | {ping}ms | /about"
                await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
        except: pass

    @tasks.loop(seconds=30)
    async def status_task(self):
        await self.update_status()
    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    async def send_log(self, guild_id: int, title: str, description: str, color: discord.Color, fields: list = None):
        config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data or not config_data.get('log_channel_id'): return
        try:
            log_channel = self.get_channel(int(config_data['log_channel_id']))
            if not log_channel: return
            embed = discord.Embed(title=title, description=description, color=color)
            if fields:
                for name, value in fields: embed.add_field(name=name, value=value, inline=True)
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
            for n, v in fields: embed.add_field(name=n, value=v, inline=True)
        embed.set_footer(text="Chronis System")
        return await channel.send(embed=embed)

    @tasks.loop(time=datetime.time(hour=4, minute=0))
    async def scheduled_restart(self):
        print("⏰ 04h00 : Maintenance...")
        restart_data = {"manual_channel_id": None, "manual_message_id": None, "log_messages": []}
        try:
            configs = await self.db.get_all_guild_configs()
            for config_data in configs:
                guild_id = int(config_data['guild_id'])
                active = await self.db.get_all_active_sessions(str(guild_id))
                if active:
                    for s in active: await self.db.end_session(s['user_id'], str(guild_id))
                    await self.update_service_message(guild_id, config_data)
            
            txt = config.TRANSLATIONS['fr']
            msg = await self.send_system_log(txt['log_maint_title'], txt['log_maint_desc'], discord.Color.gold(), [(txt['log_duration_est'], "~5 minutes")])
            if msg: restart_data["log_messages"].append({"channel_id": msg.channel.id, "message_id": msg.id})
        except: pass
        
        try:
            with open("restart_context.json", "w") as f:
                json.dump(restart_data, f)
        except: pass
            
        self.maintenance_mode = True
        await self.update_status()
        await self.close()

    async def update_service_message(self, guild_id: int, config_data: dict = None):
        if not config_data: config_data = await self.db.get_guild_config(str(guild_id))
        if not config_data: return
        try:
            channel = self.get_channel(int(config_data['channel_id']))
            if not channel: return
            active = await self.db.get_all_active_sessions(str(guild_id))
            is_maint = int(config_data.get('is_maintenance', 0)) == 1
            from utils import create_service_embed
            lang = config_data.get('language', 'fr')
            embed = create_service_embed(active, channel.guild, lang, is_maint)
            message = channel.get_partial_message(int(config_data['message_id']))
            await message.edit(embed=embed)
        except: pass

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token: return print("❌ ERREUR TOKEN")
    bot = ChronosBot()

    # --- CHECK BLACKLIST GLOBAL (Commandes Texte) ---
    @bot.check
    async def globally_block_blacklisted(ctx):
        if await bot.db.is_blacklisted(str(ctx.author.id)):
            return False
        return True

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def sync(ctx):
        import config as cfg
        lang = await bot.get_guild_lang(ctx.guild.id)
        txt = cfg.TRANSLATIONS[lang]
        msg = await ctx.send(txt['cmd_sync_start'])
        try:
            s = await bot.tree.sync()
            await msg.edit(content=txt['cmd_sync_end'].format(count=len(s)))
            user_display = f"{ctx.author.name} ({ctx.author.id})"
            await bot.send_system_log(txt['log_sync_title'], txt['log_sync_desc'].format(user=user_display), discord.Color.purple(), [("Status", txt['log_stat_done'])])
        except Exception as e: await msg.edit(content=f"❌ Error: `{e}`")

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def restart(ctx):
        import config as cfg
        lang = await bot.get_guild_lang(ctx.guild.id)
        txt = cfg.TRANSLATIONS[lang]
        msg = await ctx.send(txt['cmd_restart_start'])
        restart_data = {"manual_channel_id": ctx.channel.id, "manual_message_id": msg.id, "log_messages": []}
        
        user_display = f"{ctx.author.name} ({ctx.author.id})"
        log_msg = await bot.send_system_log(txt['log_restart_title'], txt['log_restart_desc'].format(user=user_display), discord.Color.gold(), [("Status", txt['log_stat_wip'])])
        if log_msg: restart_data["log_messages"].append({"channel_id": log_msg.channel.id, "message_id": log_msg.id})

        try:
            with open("restart_context.json", "w") as f:
                json.dump(restart_data, f)
        except: pass
        
        await bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # --- MAINTENANCE (CORRIGÉE : Argument Optionnel) ---
    @bot.command()
    @commands.is_owner()
    async def maintenance(ctx, state: str = None):
        """Active/Désactive la maintenance GLOBALE"""
        import config as cfg
        
        # Si aucun argument, on affiche l'aide
        if state is None:
            return await ctx.send("❌ Usage: `+maintenance on` ou `+maintenance off`")

        state = state.lower()
        if state not in ["on", "off"]:
            return await ctx.send("❌ Usage: `+maintenance on` ou `+maintenance off`")
            
        new_val = 1 if state == "on" else 0
        bot.maintenance_mode = (new_val == 1) # Variable locale
        await bot.update_status()
        
        # DB Globale
        await bot.db.set_global_maintenance(new_val)
        
        # Update tous les serveurs
        configs = await bot.db.get_all_guild_configs()
        count = 0
        for c in configs:
            c['is_maintenance'] = new_val 
            await bot.update_service_message(int(c['guild_id']), c)
            count += 1
            
        lang = await bot.get_guild_lang(ctx.guild.id)
        txt = cfg.TRANSLATIONS[lang]
        msg = txt['maint_enabled'] if new_val else txt['maint_disabled']
        
        await bot.send_system_log("🚧 Maintenance", f"Mode {state.upper()} appliqué sur {count} serveurs.", discord.Color.orange())
        await ctx.send(f"{msg} ({count} serveurs mis à jour)")

    @bot.command()
    @commands.is_owner()
    async def stop(ctx):
        import config as cfg
        await ctx.send("🛑")
        txt = cfg.TRANSLATIONS['fr']
        await bot.send_system_log(txt['log_bot_stop_title'], txt['log_bot_stop_desc'], discord.Color.red())
        await bot.close()
        sys.exit(0)

    @bot.command()
    @commands.is_owner()
    async def start(ctx):
        import config as cfg
        await ctx.send("🟢")
        txt = cfg.TRANSLATIONS['fr']
        await bot.send_system_log(txt['log_bot_start_title'], txt['log_bot_start_desc'], discord.Color.green())

    # --- BLACKLIST & INFOS ---
    @bot.command()
    @commands.is_owner()
    async def bl(ctx, user_id: str):
        import config as cfg
        txt = cfg.TRANSLATIONS['fr']
        if await bot.db.is_blacklisted(user_id):
            return await ctx.send(txt['bl_already'])
        await bot.db.add_blacklist(user_id)
        await ctx.send(txt['bl_add_success'].format(user=user_id))
        await bot.send_system_log("⛔ Blacklist", f"User {user_id} ajouté.", discord.Color.red())

    @bot.command()
    @commands.is_owner()
    async def unbl(ctx, user_id: str):
        import config as cfg
        txt = cfg.TRANSLATIONS['fr']
        if not await bot.db.is_blacklisted(user_id):
            return await ctx.send(txt['bl_not_found'])
        await bot.db.remove_blacklist(user_id)
        await ctx.send(txt['bl_remove_success'].format(user=user_id))
        await bot.send_system_log("✅ Un-Blacklist", f"User {user_id} retiré.", discord.Color.green())

    @bot.command()
    @commands.is_owner()
    async def infos(ctx):
        import config as cfg
        txt = cfg.TRANSLATIONS['fr']
        guild_count = len(bot.guilds)
        # Affiche les 20 premiers serveurs
        s_list = "\n".join([f"• {g.name} (`{g.id}`) - {g.member_count}" for g in bot.guilds[:20]])
        if len(bot.guilds) > 20: s_list += f"\n... et {len(bot.guilds)-20} autres."
        
        embed = discord.Embed(title=txt['infos_title'], description=txt['infos_desc'].format(count=guild_count), color=config.BOT_COLOR)
        embed.add_field(name="Serveurs", value=s_list or "Aucun", inline=False)
        await ctx.send(embed=embed)

    try: bot.run(token)
    except KeyboardInterrupt: pass
    if bot.maintenance_mode:
        time.sleep(300)
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()