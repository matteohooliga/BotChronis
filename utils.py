from datetime import datetime
from typing import Dict, Any
import discord
import config

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

def create_service_embed(active_sessions: list, guild: discord.Guild, lang: str = 'fr') -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    
    embed = discord.Embed(title=f"{texts['embed_title']} – ({len(active_sessions)})", color=config.BOT_COLOR)
    
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
                if session['is_paused'] and session['pause_start']:
                    elapsed -= (now - session['pause_start'])
                
                user_list.append(f"{status_icon} {user.mention} {texts['embed_since']} {start_time} • `{format_duration(elapsed)}`")
        
        embed.description = "\n".join(user_list)
    
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_stats_embed(stats: Dict[str, Any], user: discord.User, lang: str = 'fr') -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    
    embed = discord.Embed(title=texts['stats_title'].format(name=user.display_name), color=config.BOT_COLOR)
    
    if not stats or stats['total_sessions'] == 0:
        embed.description = texts['stats_no_data']
        return embed
    
    fields = texts['stats_fields']
    embed.add_field(name=fields[0], value=f"`{stats['total_sessions']}`", inline=True)
    embed.add_field(name=fields[1], value=f"`{format_duration(stats['total_time'] or 0)}`", inline=True)
    embed.add_field(name=fields[2], value=f"`{format_duration(stats['avg_time'] or 0)}`", inline=True)
    embed.add_field(name=fields[3], value=f"`{format_duration(stats['max_time'] or 0)}`", inline=True)
    embed.add_field(name=fields[4], value=f"`{format_duration(stats['min_time'] or 0)}`", inline=True)
    
    if user.display_avatar: embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def create_all_stats_embed(all_stats: list, guild: discord.Guild, lang: str = 'fr') -> discord.Embed:
    texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
    
    embed = discord.Embed(title=texts['global_title'].format(guild=guild.name), color=config.BOT_COLOR)
    
    if not all_stats:
        embed.description = texts['stats_no_data']
        return embed
    
    top = all_stats[:10]
    description_lines = []
    for i, s in enumerate(top, 1):
        try:
            # Tente de récupérer l'objet membre pour la mention
            user = guild.get_member(int(s['user_id']))
            # Utilisation de user.mention si disponible, sinon le nom stocké
            name_display = user.mention if user else s['username']
        except: name_display = s['username']
        
        medal = "🥇 " if i==1 else "🥈 " if i==2 else "🥉 " if i==3 else ""
        description_lines.append(f"{medal}**{i}.** {name_display} • `{format_duration(s['total_time'] or 0)}`")
    
    embed.description = "\n".join(description_lines)
    
    fields = texts['global_fields']
    total_s = sum(s['total_sessions'] for s in all_stats)
    total_t = sum(s['total_time'] or 0 for s in all_stats)
    embed.add_field(name=fields[0], value=f"`{total_s}`", inline=True)
    embed.add_field(name=fields[1], value=f"`{format_duration(total_t)}`", inline=True)
    embed.add_field(name=fields[2], value=f"`{len(all_stats)}`", inline=True)

    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed

def check_permissions(member: discord.Member, allowed_roles: list = None) -> bool:
    if member.guild_permissions.administrator: return True
    if not allowed_roles: return True
    member_roles = [str(role.id) for role in member.roles]
    return any(r in allowed_roles for r in member_roles)