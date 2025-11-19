
from datetime import datetime, timedelta
from typing import Dict, Any
import discord
import config


def format_duration(milliseconds: int) -> str:
    """
    Formater une durée en millisecondes en format lisible
    
    Args:
        milliseconds: Durée en millisecondes
        
    Returns:
        Chaîne formatée (ex: "2h 30m 15s")
    """
    if milliseconds is None or milliseconds < 0:
        return "0s"
    
    seconds = milliseconds // 1000
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or len(parts) == 0:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_timestamp(timestamp: int, format_type: str = "f") -> str:
    """
    Formater un timestamp Discord
    
    Args:
        timestamp: Timestamp en millisecondes
        format_type: Type de format Discord (f, F, t, T, d, D, R)
        
    Returns:
        Timestamp formaté pour Discord
    """
    seconds = timestamp // 1000
    return f"<t:{seconds}:{format_type}>"


def create_service_embed(active_sessions: list, guild: discord.Guild) -> discord.Embed:
    """
    Créer l'embed principal du système de service
    
    Args:
        active_sessions: Liste des sessions actives
        guild: Le serveur Discord
        
    Returns:
        Embed Discord configuré
    """
    embed = discord.Embed(
        title=f"{config.EMBED_TITLE} – ({len(active_sessions)})",
        color=config.BOT_COLOR
    )
    
    if not active_sessions:
        embed.description = config.EMBED_DESCRIPTION_EMPTY
    else:
        # Construire la liste des utilisateurs en service
        user_list = []
        for session in active_sessions:
            user = guild.get_member(int(session['user_id']))
            if user:
                status_icon = "⏸️" if session['is_paused'] else "🟢"
                start_time = format_timestamp(session['start_time'], "t")
                
                # Calculer le temps écoulé
                now = int(datetime.now().timestamp() * 1000)
                elapsed = now - session['start_time'] - session['pause_duration']
                
                # Si en pause, soustraire le temps de pause en cours
                if session['is_paused'] and session['pause_start']:
                    elapsed -= (now - session['pause_start'])
                
                duration = format_duration(elapsed)
                
                user_list.append(
                    f"{status_icon} **{user.display_name}** • Depuis {start_time} • `{duration}`"
                )
        
        embed.description = "\n".join(user_list)
    
    embed.set_footer(text=config.EMBED_FOOTER)
    embed.timestamp = datetime.now()
    
    return embed


def create_service_buttons() -> discord.ui.View:
    """
    Créer les boutons de contrôle du service
    
    Returns:
        View Discord avec les boutons
    """
    view = discord.ui.View(timeout=None)
    
    # Bouton Démarrer
    start_button = discord.ui.Button(
        label=config.BUTTONS['start']['label'],
        emoji=config.BUTTONS['start']['emoji'],
        style=discord.ButtonStyle.success,
        custom_id=config.BUTTONS['start']['custom_id']
    )
    
    # Bouton Pause
    pause_button = discord.ui.Button(
        label=config.BUTTONS['pause']['label'],
        emoji=config.BUTTONS['pause']['emoji'],
        style=discord.ButtonStyle.primary,
        custom_id=config.BUTTONS['pause']['custom_id']
    )
    
    # Bouton Terminer
    stop_button = discord.ui.Button(
        label=config.BUTTONS['stop']['label'],
        emoji=config.BUTTONS['stop']['emoji'],
        style=discord.ButtonStyle.danger,
        custom_id=config.BUTTONS['stop']['custom_id']
    )
    
    view.add_item(start_button)
    view.add_item(pause_button)
    view.add_item(stop_button)
    
    return view


def create_stats_embed(stats: Dict[str, Any], user: discord.User) -> discord.Embed:
    """
    Créer un embed de statistiques pour un utilisateur
    
    Args:
        stats: Dictionnaire contenant les statistiques
        user: L'utilisateur Discord
        
    Returns:
        Embed Discord avec les statistiques
    """
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
    
    embed.add_field(
        name="Nombre de sessions",
        value=f"`{stats['total_sessions']}`",
        inline=True
    )
    embed.add_field(
        name="Temps total",
        value=f"`{total_time}`",
        inline=True
    )
    embed.add_field(
        name="Temps moyen",
        value=f"`{avg_time}`",
        inline=True
    )
    embed.add_field(
        name="Session la plus longue",
        value=f"`{max_time}`",
        inline=True
    )
    embed.add_field(
        name="Session la plus courte",
        value=f"`{min_time}`",
        inline=True
    )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.timestamp = datetime.now()
    
    return embed


def create_all_stats_embed(all_stats: list, guild: discord.Guild) -> discord.Embed:
    """
    Créer un embed de statistiques pour tous les utilisateurs
    
    Args:
        all_stats: Liste des statistiques de tous les utilisateurs
        guild: Le serveur Discord
        
    Returns:
        Embed Discord avec les statistiques globales
    """
    embed = discord.Embed(
        title=f"📊 Statistiques globales – {guild.name}",
        color=config.BOT_COLOR
    )
    
    if not all_stats:
        embed.description = "Aucune donnée de service enregistrée."
        return embed
    
    # Limiter à 10 utilisateurs pour ne pas dépasser la limite d'embed
    top_users = all_stats[:10]
    
    description_lines = []
    for i, stats in enumerate(top_users, 1):
        user = guild.get_member(int(stats['user_id']))
        username = user.display_name if user else stats['username']
        
        total_time = format_duration(stats['total_time'] or 0)
        sessions = stats['total_sessions']
        
        medal = ""
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "
        
        description_lines.append(
            f"{medal}**{i}.** {username} • `{total_time}` • {sessions} session(s)"
        )
    
    embed.description = "\n".join(description_lines)
    
    # Statistiques globales
    total_sessions = sum(s['total_sessions'] for s in all_stats)
    total_time = sum(s['total_time'] or 0 for s in all_stats)
    
    embed.add_field(
        name="Total de sessions",
        value=f"`{total_sessions}`",
        inline=True
    )
    embed.add_field(
        name="Temps total cumulé",
        value=f"`{format_duration(total_time)}`",
        inline=True
    )
    embed.add_field(
        name="Utilisateurs actifs",
        value=f"`{len(all_stats)}`",
        inline=True
    )
    
    embed.timestamp = datetime.now()
    
    return embed


def check_permissions(member: discord.Member, allowed_roles: list = None) -> bool:
    """
    Vérifier si un membre a les permissions nécessaires
    
    Args:
        member: Le membre Discord
        allowed_roles: Liste des IDs de rôles autorisés (None = tous autorisés)
        
    Returns:
        True si autorisé, False sinon
    """
    # Les administrateurs ont toujours accès
    if member.guild_permissions.administrator:
        return True
    
    # Si aucun rôle n'est défini, tout le monde peut utiliser
    if not allowed_roles:
        return True
    
    # Vérifier si le membre a au moins un des rôles autorisés
    member_role_ids = [str(role.id) for role in member.roles]
    return any(role_id in allowed_roles for role_id in member_role_ids)
