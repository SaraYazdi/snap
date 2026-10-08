"""Functional can_access — XACML/AuthzForce deferred to security phase."""

from datetime import datetime, timezone

from app.models import CREW_CATEGORIES, ContentGrant


def _now():
    return datetime.now(timezone.utc)


def _aware(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _active_grant(user, item, action, now):
    for g in item.grants:
        if g.user_id != user.id or g.action != action or g.revoked:
            continue
        vf, vu = _aware(g.valid_from), _aware(g.valid_until)
        if vf and vf > now:
            continue
        if vu and vu < now:
            continue
        return True
    return False


def _roles(user, band_id):
    roles = set()
    for m in user.memberships:
        if m.role == "administrator" and m.band_id is None:
            roles.add("administrator")
        elif m.band_id == band_id:
            roles.add(m.role)
    return roles


def _press_window_ok(item, now):
    afp = _aware(item.available_from_press)
    return afp is None or now >= afp


def _fan_window_ok(item, now):
    aff = _aware(item.available_from_fans)
    return aff is None or now >= aff


def can_access(user, item, action):
    """Return (allowed: bool, deny_reason: str|None)."""
    if user is None or user.status != "active":
        return False, "unauthenticated"

    if item.is_deleted:
        return False, "deleted"

    now = _now()

    if _active_grant(user, item, action, now):
        return True, None

    roles = _roles(user, item.band_id)

    if "administrator" in roles and "band_member" not in roles:
        return False, "admin_needs_grant"

    if "band_member" in roles:
        return True, None

    if action == "manage":
        return False, "role"

    # Crew
    if "crew" in roles:
        if item.category in CREW_CATEGORIES or item.audience_level in ("crew", "public") or item.is_public:
            return True, None
        return False, "role"

    # Press
    if "press" in roles:
        if item.is_public or item.audience_level in ("press", "public"):
            if _press_window_ok(item, now):
                return True, None
            return False, "embargo"
        return False, "role"

    # Fan club
    if "fan_club" in roles:
        if item.is_public or item.audience_level in ("fan_club", "public"):
            if _fan_window_ok(item, now):
                return True, None
            return False, "embargo"
        return False, "role"

    # Registered (or any authenticated user with public content)
    if item.is_public or item.audience_level == "public":
        return True, None

    if item.audience_level == "restricted":
        return False, "restricted"

    return False, "role"


def can_upload(user, band_id):
    return user is not None and user.status == "active" and user.is_band_member(band_id)


def can_view_logs(user, item=None):
    if user is None or user.status != "active":
        return False
    if user.is_admin():
        return True
    if item is not None:
        return user.is_band_member(item.band_id)
    return any(m.role == "band_member" for m in user.memberships)


def can_admin(user):
    return user is not None and user.status == "active" and user.is_admin()


def log_access(db, user, item, action, allowed, deny_reason, request):
    from app.models import AccessLog

    entry = AccessLog(
        content_item_id=item.id if item else None,
        user_id=user.id if user else None,
        action=action,
        outcome="allowed" if allowed else "denied",
        ip_address=request.remote_addr if request else None,
        user_agent=(request.headers.get("User-Agent") if request else None),
        deny_reason=deny_reason,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
