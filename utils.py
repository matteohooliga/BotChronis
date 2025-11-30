from datetime import datetime, timedelta
from typing import Dict, Any, List
import discord
import config
import math
import aiohttp
import io
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

async def create_graph(sessions: list, graph_type: str, lang='fr') -> discord.File:
    if not sessions: return None
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    
    c_main = 'rgba(97, 0, 189, 0.8)'
    c_orange = 'rgba(243, 156, 18, 0.8)'
    c_green = 'rgba(46, 204, 113, 0.8)'
    c_border = 'rgba(255, 255, 255, 0.9)'

    today = datetime.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels_7d = [d.strftime("%d/%m") for d in last_7_days]
    
    chart_config = {
        "type": "bar",
        "data": {
            "labels": [],
            "datasets": [{
                "label": "Données",
                "backgroundColor": c_main,
                "borderColor": c_border,
                "borderWidth": 1,
                "data": []
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": "Graphique",
                "fontColor": "#fff",
                "fontSize": 18
            },
            "legend": {"display": False},
            "scales": {
                "xAxes": [{"ticks": {"fontColor": "#fff"}}],
                "yAxes": [{"ticks": {"fontColor": "#fff", "beginAtZero": True}}]
            }
        }
    }

    if graph_type == "weekly_hours":
        data = defaultdict(int)
        for s in sessions:
            if not s.get('start_time'): continue
            dt = datetime.fromtimestamp(s['start_time'] / 1000).date()
            if dt in last_7_days:
                data[dt.strftime("%d/%m")] += (s['total_duration'] or 0)
        
        values = [round(data[lbl] / 3600000, 1) for lbl in labels_7d]
        chart_config["data"]["labels"] = labels_7d
        chart_config["data"]["datasets"][0]["data"] = values
        chart_config["data"]["datasets"][0]["backgroundColor"] = c_main
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_hours', "Heures Cumulées (7j)")

    elif graph_type == "weekly_staff":
        data = defaultdict(set)
        for s in sessions:
            if not s.get('start_time'): continue
            dt = datetime.fromtimestamp(s['start_time'] / 1000).date()
            if dt in last_7_days:
                data[dt.strftime("%d/%m")].add(s['user_id'])
        
        values = [len(data[lbl]) for lbl in labels_7d]
        chart_config["data"]["labels"] = labels_7d
        chart_config["data"]["datasets"][0]["data"] = values
        chart_config["data"]["datasets"][0]["backgroundColor"] = c_orange
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_staff', "Effectif Unique (7j)")

    elif graph_type == "weekly_avg":
        data_dur = defaultdict(int)
        data_cnt = defaultdict(int)
        for s in sessions:
            if not s.get('start_time'): continue
            dt = datetime.fromtimestamp(s['start_time'] / 1000).date()
            if dt in last_7_days:
                lbl = dt.strftime("%d/%m")
                data_dur[lbl] += (s['total_duration'] or 0)
                data_cnt[lbl] += 1
        
        values = []
        for lbl in labels_7d:
            avg = (data_dur[lbl] / data_cnt[lbl]) / 3600000 if data_cnt[lbl] > 0 else 0
            values.append(round(avg, 1))

        chart_config["data"]["labels"] = labels_7d
        chart_config["data"]["datasets"][0]["data"] = values
        chart_config["data"]["datasets"][0]["backgroundColor"] = c_green
        chart_config["options"]["title"]["text"] = texts.get('srv_title_weekly_avg', "Temps Moyen (7j)")

    elif graph_type == "daily_activity":
        chart_config["type"] = "line"
        hourly_presence = [set() for _ in range(24)]
        
        for s in sessions:
            if not s.get('start_time') or not s.get('end_time'): continue
            start_dt = datetime.fromtimestamp(s['start_time'] / 1000)
            end_dt = datetime.fromtimestamp(s['end_time'] / 1000)
            
            curr = start_dt.replace(minute=0, second=0, microsecond=0)
            while curr <= end_dt:
                if curr == end_dt and start_dt != end_dt: break
                h = curr.hour
                day_str = curr.strftime("%Y-%m-%d")
                unique_key = f"{s['user_id']}|{day_str}"
                hourly_presence[h].add(unique_key)
                curr += timedelta(hours=1)
                if (curr - start_dt).days > 1: break

        values = [len(u_set) / 7.0 for u_set in hourly_presence]
        chart_config["data"]["labels"] = [f"{h}h" for h in range(24)]
        chart_config["data"]["datasets"][0]["data"] = values
        chart_config["data"]["datasets"][0]["label"] = "Moyenne Agents"
        chart_config["data"]["datasets"][0]["borderColor"] = "#00FFFF"
        chart_config["data"]["datasets"][0]["backgroundColor"] = "rgba(0, 255, 255, 0.2)"
        chart_config["data"]["datasets"][0]["fill"] = True
        chart_config["options"]["title"]["text"] = texts.get('srv_title_daily_activity', "Activité Moyenne (00h-23h)")

    elif graph_type == "daily_sessions":
        data = defaultdict(int)
        for s in sessions:
            if not s.get('start_time'): continue
            dt = datetime.fromtimestamp(s['start_time'] / 1000).date()
            if dt in last_7_days:
                data[dt.strftime("%d/%m")] += 1
        
        values = [data[lbl] for lbl in labels_7d]
        chart_config["data"]["labels"] = labels_7d
        chart_config["data"]["datasets"][0]["data"] = values
        chart_config["data"]["datasets"][0]["backgroundColor"] = "#FF00FF"
        chart_config["options"]["title"]["text"] = texts.get('srv_title_daily_sessions', "Sessions Lancées")

    url = "https://quickchart.io/chart"
    payload = {"chart": chart_config, "width": 800, "height": 400, "backgroundColor": "transparent"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                image_data = await response.read()
                return discord.File(io.BytesIO(image_data), filename='graph.png')
            else:
                return None

def create_service_embed(active_sessions: list, guild: discord.Guild, lang: str = 'fr', maintenance: bool = False) -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    if maintenance:
        embed = discord.Embed(title=texts['maint_embed_title'], description=texts['maint_embed_desc'], color=config.COLOR_ORANGE)
        embed.set_footer(text=config.EMBED_FOOTER)
        embed.timestamp = datetime.now()
        return embed
    color = get_dynamic_color(active_sessions)
    embed = discord.Embed(title=f"{texts['embed_title']} – ({len(active_sessions)})", color=color)
    if not active_sessions:
        embed.description = texts['embed_empty']
    else:
        user_list = []
        for session in active_sessions:
            user = guild.get_member(int(session['user_id']))
            if user:
                status_icon = "⏸️" if session['is_paused'] else "🟢"
                start_time = format_timestamp(session['start_time'], "t")
                now = int(datetime.now().timestamp() * 1000)
                elapsed = now - session['start_time'] - session['pause_duration']
                if session['is_paused'] and session['pause_start']: elapsed -= (now - session['pause_start'])
                user_list.append(f"{status_icon} {user.mention} {texts['embed_since']} {start_time} • `{format_duration(elapsed)}`")
        embed.description = "\n".join(user_list)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_stats_embed(stats: Dict[str, Any], user: discord.User, lang: str = 'fr', goal_ms: int = 0) -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    embed = discord.Embed(title=texts['stats_title'].format(name=user.display_name), color=config.BOT_COLOR)
    
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
    
    # --- AJOUT: Affichage des dates si disponibles ---
    if stats.get('first_service') and stats.get('last_service'):
        f_date = f"<t:{int(stats['first_service']/1000)}:d>" 
        l_date = f"<t:{int(stats['last_service']/1000)}:d>"
        embed.add_field(name="🗓️ Période d'activité", value=f"Du {f_date} au {l_date}", inline=False)

    if user.display_avatar: embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_all_stats_embed(all_stats: list, guild: discord.Guild, lang: str = 'fr', page: int = 1, goal_ms: int = 0, absent_users: list = None) -> (discord.Embed, int):
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    if absent_users is None: absent_users = []
    absent_ids = [str(uid) for uid in absent_users]

    ITEMS_PER_PAGE = 10
    total_pages = math.ceil(len(all_stats) / ITEMS_PER_PAGE)
    if total_pages == 0: total_pages = 1
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_stats = all_stats[start_idx:end_idx]
    
    embed = discord.Embed(title=texts['global_title'].format(guild=guild.name), color=config.BOT_COLOR)
    if not all_stats:
        embed.description = texts['stats_no_data']
        return embed, 1
    
    lines = []
    for i, s in enumerate(current_stats, start_idx + 1):
        try:
            user = guild.get_member(int(s['user_id']))
            name = user.mention if user else s['username']
        except: name = s['username']
        
        medal = "🥇 " if i==1 else "🥈 " if i==2 else "🥉 " if i==3 else ""
        warning = " ⚠️" if (goal_ms > 0 and (s['total_time'] or 0) < goal_ms) else ""
        
        absence_tag = ""
        if str(s['user_id']) in absent_ids:
            absence_tag = f" {texts.get('sumall_tag_absence', '🚫')}"
            
        lines.append(f"{medal}**{i}.** {name}{absence_tag} • `{format_duration(s['total_time'] or 0)}`{warning}")
        
    embed.description = "\n".join(lines)
    fields = texts['global_fields']
    total_s = sum(s['total_sessions'] for s in all_stats)
    total_t = sum(s['total_time'] or 0 for s in all_stats)
    embed.add_field(name=fields[0], value=f"`{total_s}`", inline=True)
    embed.add_field(name=fields[1], value=f"`{format_duration(total_t)}`", inline=True)
    embed.add_field(name=fields[2], value=f"`{len(all_stats)}`", inline=True)
    embed.set_footer(text=f"Page {page}/{total_pages} | {config.EMBED_FOOTER}")
    embed.timestamp = datetime.now()
    return embed, total_pages

def create_server_stats_embed(stats: dict, days: float, lang: str = 'fr') -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    embed = discord.Embed(title=texts['srv_stats_title'], description=texts['srv_stats_desc'].format(days=int(days)), color=config.BOT_COLOR)
    
    global_text = f"{texts['srv_val_total_time'].format(val=format_duration(stats['total_duration']))}\n" \
                  f"{texts['srv_val_sessions'].format(val=stats['total_sessions'])}\n" \
                  f"{texts.get('srv_val_total_agents', '• Agents: `{val}`').format(val=stats['unique_users'])}"
    embed.add_field(name=texts['srv_field_global'], value=global_text, inline=False)
    
    embed.add_field(name=texts['srv_field_daily'], value=f"{texts['srv_val_people_day'].format(val=round(stats['avg_people_per_day'], 1))}\n{texts['srv_val_time_day'].format(val=format_duration(stats['avg_time_user_day']))}", inline=False)
    
    embed.add_field(name=texts['srv_field_weekly'], value=f"{texts['srv_val_time_week'].format(val=format_duration(stats['avg_time_user_week']))}", inline=False)
    
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def check_permissions(member: discord.Member, allowed_roles: list = None) -> bool:
    if member.guild_permissions.administrator: return True
    if not allowed_roles: return True
    return any(str(r.id) in allowed_roles for r in member.roles)