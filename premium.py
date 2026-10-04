"""Validation des droits Premium Chronis accordés par Discord."""

from datetime import datetime, timezone


def entitlement_is_active(entitlement, sku_id, now=None):
    now = now or datetime.now(timezone.utc)
    if entitlement.sku_id != sku_id or entitlement.deleted:
        return False
    if entitlement.starts_at is not None and entitlement.starts_at > now:
        return False
    if entitlement.ends_at is not None and entitlement.ends_at <= now:
        return False
    return True
