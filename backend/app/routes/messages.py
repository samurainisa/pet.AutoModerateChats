from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..models import Message, MessageStatus
from ..utils.auth import get_current_user, roles_required


messages_bp = Blueprint("messages", __name__, url_prefix="/api/messages")


def _parse_before(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@messages_bp.get("")
@roles_required("user")
def get_messages():
    room = request.args.get("room", "public")
    limit = min(max(int(request.args.get("limit", "50")), 1), 100)
    before = _parse_before(request.args.get("before"))
    user = get_current_user()

    visible_statuses = [MessageStatus.OK.value, MessageStatus.APPROVED_MANUAL.value]
    query = Message.query.filter(Message.room == room).filter(
        or_(Message.status.in_(visible_statuses), Message.user_id == user.id)
    )

    if before:
        query = query.filter(Message.created_at < before)

    rows = query.order_by(Message.created_at.desc()).limit(limit).all()

    items = []
    for row in rows:
        items.append(
            {
                "id": row.id,
                "author": row.author.username if row.author else None,
                "text": row.text_original,
                "timestamp": row.created_at.isoformat() if row.created_at else None,
                "status": row.status,
            }
        )

    next_before = rows[-1].created_at.isoformat() if rows else None
    return jsonify({"items": items, "next_before": next_before})

