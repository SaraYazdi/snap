from collections import OrderedDict

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import CATEGORIES, CATEGORY_LABELS, ContentItem
from app.policy import can_access

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def index():
    items = ContentItem.query.filter_by(is_deleted=False).order_by(ContentItem.created_at.desc()).all()
    visible = [i for i in items if can_access(current_user, i, "view")[0]]

    # Use "entries" not "items" — Jinja treats .items as dict.items()
    sections = OrderedDict(
        (key, {"label": CATEGORY_LABELS[key], "entries": []}) for key in CATEGORIES
    )
    orphan = []
    for item in visible:
        if item.category in sections:
            sections[item.category]["entries"].append(item)
        else:
            orphan.append(item)

    has_content = any(s["entries"] for s in sections.values()) or bool(orphan)
    return render_template(
        "dashboard.html",
        sections=sections,
        orphan=orphan,
        has_content=has_content,
        is_admin=current_user.is_admin(),
        can_upload=any(m.role == "band_member" for m in current_user.memberships),
    )
