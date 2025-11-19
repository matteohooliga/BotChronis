from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import discord
import config

def format_duration(milliseconds: int) -> str:
    """
    Formater une durée en millisecondes en format lisible (Optimisé)
    """
    if not milliseconds or milliseconds < 0:
        return "0s"
    
    seconds = int(milliseconds / 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def format_timestamp(timestamp: int, format_type: str = "f") -> str:
    """Formater un timestamp Discord"""
    seconds = timestamp // 1000
    return f"<t:{seconds}:{format_type}>"

def create_service_embed(active_sessions: list, guild: discord.Guild) -> discord.Embed:
    """Créer l'embed principal du système de service"""
    embed = discord.Embed(
        title=f"{config.EMBED_TITLE} – ({len(active_sessions)})",
        color=config.BOT_COLOR
    )
    
    if not active_sessions:
        embed.description = config.EMBED_DESCRIPTION_EMPTY
    else:
        user_list = []
        for session in active_sessions:
            # Récupération du membre
            user = guild.get_member(int(session['user_id']))
            if user:
                status_icon = "⏸️" if session['is_paused'] else "🟢"
                start_time = format_timestamp(session['start_time'], "t")
                
                now = int(datetime.now().timestamp() * 1000)
                elapsed = now - session['start_time'] - session['pause_duration']
                
                if session['is_paused'] and session['pause_start']:
                    elapsed -= (now - session['pause_start'])
                
                duration = format_duration(elapsed)
                
                # MODIFICATION ICI : user.mention rend le pseudo cliquable
                user_list.append(
                    f"{status_icon} {user.mention} • Depuis {start_time} • `{duration}`"
                )
        
        embed.description = "\n".join(user_list)
    
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    
    return embed

def create_service_buttons() -> discord.ui.View:
    """Créer les boutons de contrôle du service (pour setup initial)"""
    view = discord.ui.View(timeout=None)
    return view

def create_stats_embed(stats: Dict[str, Any], user: discord.User) -> discord.Embed:
    """Créer un embed de statistiques pour un utilisateur"""
    embed = discord.Embed(
        title=f"📊 Statistiques de {user.display_name}",
        color=config.BOT_COLOR
    )
    
    if not stats or stats['total_sessions'] == 0:
        embed.description = "Aucune donnée de service enregistrée."
        return embed
    
    total_time = format_duration(stats['total_time'] or 0)
    avg_time = format_duration(stats['avg_time'] or 0)
    max_time = format_duration(stats['max_time'] or 0)
    min_time = format_duration(stats['min_time'] or 0)
    
    embed.add_field(name="Nombre de sessions", value=f"`{stats['total_sessions']}`", inline=True)
    embed.add_field(name="Temps total", value=f"`{total_time}`", inline=True)
    embed.add_field(name="Temps moyen", value=f"`{avg_time}`", inline=True)
    embed.add_field(name="Session la plus longue", value=f"`{max_time}`", inline=True)
    embed.add_field(name="Session la plus courte", value=f"`{min_time}`", inline=True)
    
    if user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)
    embed.timestamp = datetime.now()
    
    return embed

def create_all_stats_embed(all_stats: list, guild: discord.Guild) -> discord.Embed:
    """Créer un embed de statistiques pour tous les utilisateurs"""
    embed = discord.Embed(
        title=f"📊 Statistiques globales – {guild.name}",
        color=config.BOT_COLOR
    )
    
    if not all_stats:
        embed.description = "Aucune donnée de service enregistrée."
        return embed
    
    top_users = all_stats[:10]
    
    description_lines = []
    for i, stats in enumerate(top_users, 1):
        try:
            user = guild.get_member(int(stats['user_id']))
            username = user.display_name if user else stats['username']
        except:
            username = stats['username']
        
        total_time = format_duration(stats['total_time'] or 0)
        sessions = stats['total_sessions']
        
        medal = ""
        if i == 1: medal = "🥇 "
        elif i == 2: medal = "🥈 "
        elif i == 3: medal = "🥉 "
        
        description_lines.append(
            f"{medal}**{i}.** {username} • `{total_time}` • {sessions} session(s)"
        )
    
    embed.description = "\n".join(description_lines)
    
    total_sessions = sum(s['total_sessions'] for s in all_stats)
    total_time_sum = sum(s['total_time'] or 0 for s in all_stats)
    
    embed.add_field(name="Total de sessions", value=f"`{total_sessions}`", inline=True)
    embed.add_field(name="Temps total cumulé", value=f"`{format_duration(total_time_sum)}`", inline=True)
    embed.add_field(name="Utilisateurs actifs", value=f"`{len(all_stats)}`", inline=True)
    
    embed.timestamp = datetime.now()
    return embed

def check_permissions(member: discord.Member, allowed_roles: Optional[List[str]] = None) -> bool:
    """Vérifier si un membre a les permissions nécessaires"""
    if member.guild_permissions.administrator:
        return True
    
    if not allowed_roles:
        return True
    
    member_role_ids = [str(role.id) for role in member.roles]
    return any(role_id in allowed_roles for role_id in member_role_ids)