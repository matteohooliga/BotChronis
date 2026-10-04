import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import discord
import aiohttp
import io
import config
from collections import defaultdict

def format_duration(milliseconds: int) -> str:
    if not milliseconds or milliseconds < 0: return "0s"
    seconds = int(milliseconds / 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0 or not parts: parts.append(f"{seconds}s")
    return " ".join(parts)

def format_timestamp(timestamp: int, format_type: str = "f") -> str:
    return f"<t:{timestamp // 1000}:{format_type}>"

def get_dynamic_color(active_sessions: list) -> int:
    if any(s['is_paused'] for s in active_sessions): return config.COLOR_BLUE
    if len(active_sessions) >= config.THRESHOLD_LOW: return config.COLOR_GREEN
    return config.COLOR_RED

def int_to_hex(color_int):
    return f"#{color_int:06x}"

async def has_voted_topgg(user_id: str) -> bool:
    token = os.getenv("TOPGG_TOKEN")
    if not token: return False
    url = f"https://top.gg/api/bots/1440743920953725118/check?userId={user_id}" 
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": token}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("voted", 0) == 1
    except Exception as e:
        print(f"[ERREUR utils.has_voted_topgg]: {e}")
    return False

async def generate_transcript_file(channel: discord.TextChannel, closer: discord.User = None, reason: str = None):
    messages = [m async for m in channel.history(limit=None, oldest_first=True)]
    lines = []
    lines.append("---- LOG DE TICKET ----")
    lines.append(f"Salon : {channel.name}")
    lines.append(f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if closer: lines.append(f"Fermé par : {closer.display_name} ({closer.id})")
    if reason: lines.append(f"Raison de fermeture : {reason}")
    lines.append("-" * 30 + "\n") 
    
    for msg in messages:
        timestamp = msg.created_at.strftime('%d/%m/%Y %H:%M')
        content = msg.content
        if msg.embeds:
            for embed in msg.embeds:
                title = embed.title if embed.title else (embed.description[:20] + "..." if embed.description else "Embed sans titre")
                content += f"\n<EMBED {title}>"
        if msg.attachments:
            for attachment in msg.attachments:
                content += f"\n{attachment.url}"
        lines.append(f"{timestamp} - {msg.author.display_name}: {content}\n") 
        
    return discord.File(io.BytesIO("\n".join(lines).encode('utf-8')), filename=f"transcript-{channel.name}.txt")

async def create_graph(sessions: list, graph_type: str, lang='fr', target_date=None) -> discord.File:
    if not sessions and graph_type != "hourly_specific_day": return None
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    c_main, c_orange, c_green, c_border = 'rgba(97, 0, 189, 0.8)', 'rgba(243, 156, 18, 0.8)', 'rgba(46, 204, 113, 0.8)', 'rgba(255, 255, 255, 0.9)'
    last_7_days = [datetime.now().date() - timedelta(days=i) for i in range(6, -1, -1)]
    labels_7d = [d.strftime("%d/%m") for d in last_7_days]
    
    chart_config = {
        "type": "bar", "data": {"labels": [], "datasets": [{"label": "Données", "backgroundColor": c_main, "borderColor": c_border, "borderWidth": 1, "data": []}]},
        "options": {"title": {"display": True, "text": "Graphique", "fontColor": "#fff", "fontSize": 18}, "legend": {"display": False}, "scales": {"xAxes": [{"ticks": {"fontColor": "#fff"}}], "yAxes": [{"ticks": {"fontColor": "#fff", "beginAtZero": True}}]}}
    }

    if graph_type == "weekly_hours":
        data = defaultdict(int)
        for s in sessions:
            if s.get('start_time') and datetime.fromtimestamp(s['start_time']/1000).date() in last_7_days:
                data[datetime.fromtimestamp(s['start_time']/1000).date().strftime("%d/%m")] += (s['total_duration'] or 0)
        chart_config["data"]["labels"] = labels_7d
        chart_config["data"]["datasets"][0]["data"] = [round(data[lbl]/3600000, 1) for lbl in labels_7d]
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_hours', "Heures Cumulées")
    elif graph_type == "weekly_staff":
        data = defaultdict(set)
        for s in sessions:
            if s.get('start_time') and datetime.fromtimestamp(s['start_time']/1000).date() in last_7_days:
                data[datetime.fromtimestamp(s['start_time']/1000).date().strftime("%d/%m")].add(s['user_id'])
        chart_config["data"]["labels"], chart_config["data"]["datasets"][0]["data"], chart_config["data"]["datasets"][0]["backgroundColor"] = labels_7d, [len(data[lbl]) for lbl in labels_7d], c_orange
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_staff', "Effectif")
    elif graph_type == "weekly_avg":
        data_dur, data_cnt = defaultdict(int), defaultdict(int)
        for s in sessions:
            if s.get('start_time') and datetime.fromtimestamp(s['start_time']/1000).date() in last_7_days:
                lbl = datetime.fromtimestamp(s['start_time']/1000).date().strftime("%d/%m")
                data_dur[lbl] += (s['total_duration'] or 0)
                data_cnt[lbl] += 1
        chart_config["data"]["labels"], chart_config["data"]["datasets"][0]["data"], chart_config["data"]["datasets"][0]["backgroundColor"] = labels_7d, [round(((data_dur[lbl]/data_cnt[lbl])/3600000 if data_cnt[lbl] > 0 else 0), 1) for lbl in labels_7d], c_green
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_avg', "Temps Moyen")
    elif graph_type == "daily_activity":
        chart_config["type"] = "line"
        hourly_presence = [set() for _ in range(24)]
        for s in sessions:
            if not s.get('start_time') or not s.get('end_time'): continue
            end_ts = int(datetime.now().timestamp()*1000) if s['is_active'] else s.get('end_time')
            start_dt, end_dt = datetime.fromtimestamp(s['start_time']/1000), datetime.fromtimestamp(end_ts/1000)
            curr = start_dt.replace(minute=0, second=0, microsecond=0)
            while curr <= end_dt:
                if curr == end_dt and start_dt != end_dt: break
                hourly_presence[curr.hour].add(f"{s['user_id']}|{curr.strftime('%Y-%m-%d')}")
                curr += timedelta(hours=1)
                if (curr - start_dt).days > 1: break
        chart_config["data"]["labels"], chart_config["data"]["datasets"][0]["data"], chart_config["data"]["datasets"][0]["borderColor"], chart_config["data"]["datasets"][0]["backgroundColor"], chart_config["options"]["title"]["text"] = [f"{h}h" for h in range(24)], [len(u)/7.0 for u in hourly_presence], "#00FFFF", "rgba(0, 255, 255, 0.2)", texts.get('srv_title_daily_activity', "Activité Moyenne")

    url = "https://quickchart.io/chart"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"chart": chart_config, "width": 800, "height": 400, "backgroundColor": "transparent"}) as response:
                if response.status == 200: return discord.File(io.BytesIO(await response.read()), filename='graph.png')
    except Exception as e: print(f"[ERREUR utils.create_graph] QuickChart: {e}")
    return None

def create_service_embed(active_sessions: list, guild: discord.Guild, lang: str = 'fr', maintenance: bool = False) -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    if maintenance:
        embed = discord.Embed(title=texts['maint_embed_title'], description=texts['maint_embed_desc'], color=config.COLOR_ORANGE)
        embed.set_footer(text=config.EMBED_FOOTER)
        embed.timestamp = datetime.now()
        return embed
    embed = discord.Embed(title=f"{texts['embed_title']} – ({len(active_sessions)})", color=get_dynamic_color(active_sessions))
    if not active_sessions: embed.description = texts['embed_empty']
    else:
        user_list = []
        for s in active_sessions:
            try: user = guild.get_member(int(s['user_id']))
            except: user = None
            if user:
                elapsed = int(datetime.now().timestamp()*1000) - s['start_time'] - s['pause_duration']
                if s['is_paused'] and s['pause_start']: elapsed -= (int(datetime.now().timestamp()*1000) - s['pause_start'])
                user_list.append(f"{'⏸️' if s['is_paused'] else '🟢'} {user.mention} {texts['embed_since']} {format_timestamp(s['start_time'], 't')} • `{format_duration(elapsed)}`")
        embed.description = "\n".join(user_list)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_stats_embed(stats: Dict[str, Any], user: discord.User, lang: str = 'fr', goal_ms: int = 0, bot_color: int = config.BOT_COLOR) -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    embed = discord.Embed(title=texts['stats_title'].format(name=user.display_name), color=bot_color)
    total_ms = stats['total_time'] or 0
    if goal_ms > 0 and total_ms < goal_ms: 
        embed.description = f"**{texts['goal_warning_title']}**\n{texts['goal_warning_desc'].format(goal=format_duration(goal_ms))}\n\n"
        embed.color = config.COLOR_RED
    elif not stats or stats['total_sessions'] == 0: 
        embed.description = texts['stats_no_data']
        return embed
    fields = texts['stats_fields']
    embed.add_field(name=fields[0], value=f"`{stats['total_sessions']}`", inline=True)
    embed.add_field(name=fields[1], value=f"`{format_duration(total_ms)}`", inline=True)
    embed.add_field(name=fields[2], value=f"`{format_duration(stats['avg_time'] or 0)}`", inline=True)
    embed.add_field(name=fields[3], value=f"`{format_duration(stats['max_time'] or 0)}`", inline=True)
    embed.add_field(name=fields[4], value=f"`{format_duration(stats['min_time'] or 0)}`", inline=True)
    if stats.get('first_service') and stats.get('last_service'): 
        embed.add_field(name="🗓️ Période d'activité", value=f"Du <t:{int(stats['first_service']/1000)}:d> au <t:{int(stats['last_service']/1000)}:d>", inline=False)
    if user.display_avatar: embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_all_stats_embed(all_stats: list, guild: discord.Guild, lang: str = 'fr', page: int = 1, goal_ms: int = 0, absent_users: list = None, bot_color: int = config.BOT_COLOR) -> (discord.Embed, int):
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    absent_ids = [str(uid) for uid in (absent_users or [])]
    total_pages = max(1, __import__('math').ceil(len(all_stats) / 10))
    current_stats = all_stats[(page - 1) * 10 : page * 10]
    embed = discord.Embed(title=texts['global_title'].format(guild=guild.name), color=bot_color)
    if not all_stats: 
        embed.description = texts['stats_no_data']
        return embed, 1
    
    absence_text = texts.get('sumall_tag_absence', '🚫')
    lines = []
    for i, s in enumerate(current_stats, ((page - 1) * 10) + 1):
        try: user = guild.get_member(int(s['user_id']))
        except: user = None
        name = user.mention if user else s['username']
        medal = '🥇 ' if i == 1 else ('🥈 ' if i == 2 else ('🥉 ' if i == 3 else ''))
        abs_tag = f" {absence_text}" if str(s['user_id']) in absent_ids else ""
        warning = " ⚠️" if (goal_ms > 0 and (s['total_time'] or 0) < goal_ms) else ""
        lines.append(f"{medal}**{i}.** {name}{abs_tag} • `{format_duration(s['total_time'] or 0)}`{warning}")
        
    embed.description = "\n".join(lines)
    embed.add_field(name=texts['global_fields'][0], value=f"`{sum(s['total_sessions'] for s in all_stats)}`", inline=True)
    embed.add_field(name=texts['global_fields'][1], value=f"`{format_duration(sum(s['total_time'] or 0 for s in all_stats))}`", inline=True)
    embed.add_field(name=texts['global_fields'][2], value=f"`{len(all_stats)}`", inline=True)
    embed.set_footer(text=f"Page {page}/{total_pages} | {config.EMBED_FOOTER}")
    embed.timestamp = datetime.now()
    return embed, total_pages

def create_server_stats_embed(stats: dict, days: float, lang: str = 'fr', bot_color: int = config.BOT_COLOR) -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    embed = discord.Embed(title=texts['srv_stats_title'], description=texts['srv_stats_desc'].format(days=int(days)), color=bot_color)
    embed.add_field(name=texts['srv_field_global'], value=f"{texts['srv_val_total_time'].format(val=format_duration(stats['total_duration']))}\n{texts['srv_val_sessions'].format(val=stats['total_sessions'])}\n{texts.get('srv_val_total_agents', '• Agents: `{val}`').format(val=stats['unique_users'])}", inline=False)
    embed.add_field(name=texts['srv_field_daily'], value=f"{texts['srv_val_people_day'].format(val=round(stats['avg_people_per_day'], 1))}\n{texts['srv_val_time_day'].format(val=format_duration(stats['avg_time_user_day']))}", inline=False)
    embed.add_field(name=texts['srv_field_weekly'], value=f"{texts['srv_val_time_week'].format(val=format_duration(stats['avg_time_user_week']))}", inline=False)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def check_permissions(member: discord.Member, allowed_roles: list = None) -> bool:
    if member.guild_permissions.administrator: return True
    if not allowed_roles: return True
    return any(str(r.id) in allowed_roles for r in member.roles)