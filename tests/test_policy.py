"""Minimal self-check for can_access rules."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.policy import can_access


def _user(*roles, band_id="band-1", status="active"):
    memberships = []
    for r in roles:
        memberships.append(
            SimpleNamespace(role=r, band_id=None if r == "administrator" else band_id)
        )
    return SimpleNamespace(id="u1", status=status, memberships=memberships)


def _item(**kwargs):
    defaults = dict(
        id="c1",
        band_id="band-1",
        is_deleted=False,
        is_public=False,
        audience_level="band",
        category="demo",
        available_from_press=None,
        available_from_fans=None,
        grants=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_band_member_full_access():
    u, i = _user("band_member"), _item(audience_level="restricted")
    assert can_access(u, i, "manage")[0] is True
    assert can_access(u, i, "download")[0] is True


def test_admin_denied_without_grant():
    u, i = _user("administrator"), _item()
    assert can_access(u, i, "view") == (False, "admin_needs_grant")


def test_admin_allowed_with_grant():
    now = datetime.now(timezone.utc)
    grant = SimpleNamespace(
        user_id="u1", action="view", revoked=False, valid_from=None, valid_until=None
    )
    u, i = _user("administrator"), _item(grants=[grant])
    assert can_access(u, i, "view")[0] is True


def test_press_embargo():
    future = datetime.now(timezone.utc) + timedelta(days=3)
    u = _user("press")
    i = _item(audience_level="press", available_from_press=future)
    assert can_access(u, i, "view") == (False, "embargo")


def test_registered_public_only():
    u = _user("registered")
    assert can_access(u, _item(audience_level="public", is_public=True), "view")[0] is True
    assert can_access(u, _item(audience_level="band"), "view")[0] is False


def test_crew_categories():
    u = _user("crew")
    assert can_access(u, _item(category="tour_rider", audience_level="crew"), "view")[0] is True
    assert can_access(u, _item(category="demo", audience_level="band"), "view")[0] is False


def test_deleted_denied():
    u, i = _user("band_member"), _item(is_deleted=True)
    assert can_access(u, i, "view") == (False, "deleted")
