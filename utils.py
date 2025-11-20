from datetime import datetime
from typing import Dict, Any
import discord
import config
import math

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
    
    if user.display_avatar: embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_all_stats_embed(all_stats: list, guild: discord.Guild, lang: str = 'fr', page: int = 1) -> (discord.Embed, int):
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
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
        lines.append(f"{medal}**{i}.** {name} • `{format_duration(s['total_time'] or 0)}`")
    
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

def check_permissions(member: discord.Member, allowed_roles: list = None) -> bool:
    if member.guild_permissions.administrator: return True
    if not allowed_roles: return True
    return any(str(r.id) in allowed_roles for r in member.roles)