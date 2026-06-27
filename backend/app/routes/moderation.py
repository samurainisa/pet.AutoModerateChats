from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, jsonify, request

from ..extensions import db, socketio
from ..models import Message, MessageStatus, ModerationAction, User, Violation
from ..services.rating_service import RatingService
from ..utils.auth import get_current_user, roles_required


moderation_bp = Blueprint("moderation", __name__, url_prefix="/api/moderation")


@moderation_bp.get("/queue")
@roles_required("moderator")
def queue():
    limit = min(max(int(request.args.get("limit", "100")), 1), 200)
    min_score = request.args.get("min_score")
    max_score = request.args.get("max_score")

    query = Message.query.filter(Message.status == MessageStatus.HIDDEN.value).order_by(Message.created_at.desc())

    if min_score is not None:
        query = query.filter(Message.toxicity_score >= float(min_score))
    if max_score is not None:
        query = query.filter(Message.toxicity_score <= float(max_score))

    rows = query.limit(limit).all()
    items = [
        {
            "id": row.id,
            "text": row.text_original,
            "author": row.author.username if row.author else None,
            "author_id": row.user_id,
            "score": row.toxicity_score,
            "reason": row.decision_reason,
            "rule_triggered": row.rule_triggered,
            "timestamp": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
    return jsonify({"items": items})


@moderation_bp.post("/messages/<int:message_id>/approve")
@roles_required("moderator")
def approve_message(message_id: int):
    moderator = get_current_user()
    message = db.session.get(Message, message_id)
    if message is None:
        abort(404)
    if message.status != MessageStatus.HIDDEN.value:
        return jsonify({"error": "invalid_status"}), 400
    payload = request.get_json(silent=True) or {}

    message.status = MessageStatus.APPROVED_MANUAL.value
    message.reviewed_by = moderator.id
    message.reviewed_at = datetime.utcnow()
    db.session.add(
        ModerationAction(
            message_id=message.id,
            moderator_id=moderator.id,
            action="approve",
            comment=payload.get("comment"),
        )
    )
    db.session.commit()

    socketio.emit("message_updated", {"id": message.id, "status": message.status}, namespace="/chat", room=message.room)
    socketio.emit("new_message", message.to_event_dict(), namespace="/chat", room=message.room)
    return jsonify({"ok": True, "status": message.status})


@moderation_bp.post("/messages/<int:message_id>/delete")
@roles_required("moderator")
def delete_message(message_id: int):
    moderator = get_current_user()
    message = db.session.get(Message, message_id)
    if message is None:
        abort(404)
    if message.status not in {MessageStatus.HIDDEN.value, MessageStatus.OK.value, MessageStatus.APPROVED_MANUAL.value}:
        return jsonify({"error": "invalid_status"}), 400
    payload = request.get_json(silent=True) or {}

    message.status = MessageStatus.DELETED.value
    message.reviewed_by = moderator.id
    message.reviewed_at = datetime.utcnow()
    db.session.add(
        ModerationAction(
            message_id=message.id,
            moderator_id=moderator.id,
            action="delete",
            comment=payload.get("comment"),
        )
    )
    db.session.add(
        Violation(
            user_id=message.user_id,
            message_id=message.id,
            violation_type="admin_action",
            score=message.toxicity_score,
            details_json='{"action":"delete"}',
        )
    )

    author = db.session.get(User, message.user_id)
    if author:
        rating_service = RatingService(db_session=db.session, config=current_app.config)
        rating_service.update_after_message(
            user=author, last_toxicity_score=float(message.toxicity_score or 0), message_status=MessageStatus.DELETED.value
        )

    db.session.commit()

    socketio.emit("message_updated", {"id": message.id, "status": message.status}, namespace="/chat", room=message.room)
    socketio.emit("message_updated", {"id": message.id, "status": message.status}, namespace="/chat", room="moderators")
    return jsonify({"ok": True, "status": message.status})


@moderation_bp.post("/messages/<int:message_id>/mute_user")
@roles_required("moderator")
def mute_user(message_id: int):
    moderator = get_current_user()
    message = db.session.get(Message, message_id)
    if message is None:
        abort(404)
    user = db.session.get(User, message.user_id)
    if user is None:
        abort(404)
    payload = request.get_json(silent=True) or {}

    hours = int(payload.get("hours", 24))
    user.is_blocked = True
    user.blocked_until = datetime.utcnow() + timedelta(hours=hours)

    db.session.add(
        ModerationAction(
            message_id=message.id,
            moderator_id=moderator.id,
            action="mute_user",
            comment=f"{hours}h",
        )
    )
    db.session.commit()
    return jsonify({"ok": True, "user_id": user.id, "blocked_until": user.blocked_until.isoformat()})


@moderation_bp.get("/users/<int:user_id>")
@roles_required("moderator")
def user_profile(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    messages = (
        Message.query.filter(Message.user_id == user.id)
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )
    violations = (
        Violation.query.filter(Violation.user_id == user.id)
        .order_by(Violation.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify(
        {
            "user": user.to_public_dict(),
            "messages": [
                {
                    "id": m.id,
                    "text": m.text_original,
                    "status": m.status,
                    "score": m.toxicity_score,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
            "violations": [
                {
                    "id": v.id,
                    "type": v.violation_type,
                    "score": v.score,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "details_json": v.details_json,
                }
                for v in violations
            ],
        }
    )


@moderation_bp.get("/violations")
@roles_required("moderator")
def violations_log():
    limit = min(max(int(request.args.get("limit", "100")), 1), 500)
    rows = Violation.query.order_by(Violation.created_at.desc()).limit(limit).all()
    return jsonify(
        {
            "items": [
                {
                    "id": v.id,
                    "user_id": v.user_id,
                    "username": v.user.username if v.user else None,
                    "message_id": v.message_id,
                    "type": v.violation_type,
                    "score": v.score,
                    "details_json": v.details_json,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in rows
            ]
        }
    )
