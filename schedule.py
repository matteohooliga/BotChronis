"""Calculs de calendrier indépendants de Discord et de la base de données."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def latest_due_weekly(now: datetime, weekday: int, clock: str, timezone: str = "Europe/Paris"):
    """Retourne la dernière échéance passée, y compris après une indisponibilité."""
    if weekday not in range(7):
        return None
    hour, minute = map(int, clock.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Heure hebdomadaire invalide")
    zone = ZoneInfo(timezone)
    local = now.astimezone(zone)
    candidate = (local - timedelta(days=(local.weekday() - weekday) % 7)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate > local:
        candidate -= timedelta(days=7)
    return candidate
