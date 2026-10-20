from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AccessLog, ContentItem
from app.policy import can_view_logs

bp = Blueprint("logs", __name__)


@bp.route("/logs")
@login_required
def all_logs():
    if not can_view_logs(current_user):
        abort(403)

    q = AccessLog.query.order_by(AccessLog.at.desc())
    if not current_user.is_admin():
        band_ids = [m.band_id for m in current_user.memberships if m.role == "band_member"]
        item_ids = [i.id for i in ContentItem.query.filter(ContentItem.band_id.in_(band_ids)).all()]
        q = q.filter(AccessLog.content_item_id.in_(item_ids or ["__none__"]))

    content_id = request.args.get("content_id")
    if content_id:
        q = q.filter_by(content_item_id=content_id)

    logs = q.limit(200).all()
    return render_template("logs.html", logs=logs, content_id=content_id)


@bp.route("/content/<content_id>/log")
@login_required
def item_log(content_id):
    item = db.session.get(ContentItem, content_id) or abort(404)
    if not can_view_logs(current_user, item):
        abort(403)
    logs = (
        AccessLog.query.filter_by(content_item_id=item.id)
        .order_by(AccessLog.at.desc())
        .limit(200)
        .all()
    )
    return render_template("logs.html", logs=logs, content_id=content_id, item=item)
