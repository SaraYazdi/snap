from collections import defaultdict

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import ContentItem
from app.policy import can_access

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def index():
    items = ContentItem.query.filter_by(is_deleted=False).order_by(ContentItem.created_at.desc()).all()
    visible = [i for i in items if can_access(current_user, i, "view")[0]]

    grouped = defaultdict(lambda: defaultdict(list))
    for item in visible:
        grouped[item.band.name][item.category].append(item)

    return render_template(
        "dashboard.html",
        grouped=dict(grouped),
        is_admin=current_user.is_admin(),
        can_upload=any(m.role == "band_member" for m in current_user.memberships),
    )
