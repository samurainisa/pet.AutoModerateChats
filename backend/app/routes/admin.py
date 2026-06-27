from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, jsonify, request
from sqlalchemy import case, func

from ..extensions import db
from ..models import Message, ModerationAction, Setting, User, Violation
from ..utils.auth import roles_required


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

ALLOWED_SETTINGS = {
    "low_threshold": float,
    "high_threshold": float,
    "flood_count": int,
    "flood_window": int,
    "duplicate_window": int,
    "temp_block_hours": int,
}


@admin_bp.get("/stats")
@roles_required("admin")
def stats():
    since = datetime.utcnow() - timedelta(hours=24)

    totals = (
        db.session.query(
            func.count(Message.id).label("total"),
            func.sum(case((Message.status == "ok", 1), else_=0)).label("ok_count"),
            func.sum(case((Message.status == "approved_manual", 1), else_=0)).label("approved_count"),
            func.sum(case((Message.status == "hidden", 1), else_=0)).label("hidden_count"),
            func.sum(case((Message.status == "blocked", 1), else_=0)).label("blocked_count"),
        )
        .filter(Message.created_at >= since)
        .one()
    )

    top_violators = (
        db.session.query(User.id, User.username, func.count(Violation.id).label("violations"))
        .join(Violation, Violation.user_id == User.id)
        .filter(Violation.created_at >= since)
        .group_by(User.id, User.username)
        .order_by(func.count(Violation.id).desc())
        .limit(10)
        .all()
    )

    return jsonify(
        {
            "period": "24h",
            "messages_total": int(totals.total or 0),
            "messages_ok": int((totals.ok_count or 0) + (totals.approved_count or 0)),
            "messages_hidden": int(totals.hidden_count or 0),
            "messages_blocked": int(totals.blocked_count or 0),
            "top_violators": [
                {"user_id": row.id, "username": row.username, "violations": int(row.violations or 0)}
                for row in top_violators
            ],
        }
    )


@admin_bp.patch("/settings")
@roles_required("admin")
def patch_settings():
    payload = request.get_json(silent=True) or {}
    changed = {}

    for key, converter in ALLOWED_SETTINGS.items():
        if key not in payload:
            continue
        try:
            cast_value = converter(payload[key])
        except (TypeError, ValueError):
            return jsonify({"error": f"invalid_value:{key}"}), 400

        row = db.session.get(Setting, key)
        if row is None:
            row = Setting(key=key, value=str(cast_value))
            db.session.add(row)
        else:
            row.value = str(cast_value)
        changed[key] = cast_value

    db.session.commit()
    if not changed:
        return jsonify({"ok": True, "updated": {}})

    for key, value in changed.items():
        cfg_key = key.upper()
        if cfg_key in current_app.config:
            current_app.config[cfg_key] = value

    return jsonify({"ok": True, "updated": changed})


@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    limit = min(max(int(request.args.get("limit", "100")), 1), 500)
    search_query = (request.args.get("q") or "").strip().lower()

    users_query = User.query
    if search_query:
        users_query = users_query.filter(func.lower(User.username).contains(search_query))

    users = users_query.order_by(User.created_at.desc()).limit(limit).all()
    user_ids = [user.id for user in users]

    messages_totals = {}
    violations_totals = {}
    if user_ids:
        message_rows = (
            db.session.query(Message.user_id, func.count(Message.id))
            .filter(Message.user_id.in_(user_ids))
            .group_by(Message.user_id)
            .all()
        )
        violation_rows = (
            db.session.query(Violation.user_id, func.count(Violation.id))
            .filter(Violation.user_id.in_(user_ids))
            .group_by(Violation.user_id)
            .all()
        )
        messages_totals = {int(user_id): int(total or 0) for user_id, total in message_rows}
        violations_totals = {int(user_id): int(total or 0) for user_id, total in violation_rows}

    items = []
    for user in users:
        item = user.to_public_dict()
        item.update(
            {
                "email": user.email,
                "messages_total": messages_totals.get(user.id, 0),
                "violations_total": violations_totals.get(user.id, 0),
            }
        )
        items.append(item)

    return jsonify({"items": items})


@admin_bp.get("/users/<int:user_id>")
@roles_required("admin")
def get_user_profile(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    messages = Message.query.filter(Message.user_id == user.id).order_by(Message.created_at.desc()).limit(30).all()
    violations = Violation.query.filter(Violation.user_id == user.id).order_by(Violation.created_at.desc()).limit(30).all()
    violations_total = db.session.query(func.count(Violation.id)).filter(Violation.user_id == user.id).scalar() or 0
    moderation_actions = (
        db.session.query(ModerationAction, User.username)
        .join(User, User.id == ModerationAction.moderator_id)
        .filter(ModerationAction.message_id.in_([message.id for message in messages] or [-1]))
        .order_by(ModerationAction.created_at.desc())
        .limit(30)
        .all()
    )

    status_rows = (
        db.session.query(Message.status, func.count(Message.id))
        .filter(Message.user_id == user.id)
        .group_by(Message.status)
        .all()
    )

    user_payload = user.to_public_dict()
    user_payload["email"] = user.email

    return jsonify(
        {
            "user": user_payload,
            "summary": {
                "messages_total": int(sum(int(count or 0) for _, count in status_rows)),
                "violations_total": int(violations_total),
                "status_breakdown": {status: int(count or 0) for status, count in status_rows},
            },
            "messages": [
                {
                    "id": m.id,
                    "text": m.text_original,
                    "status": m.status,
                    "score": m.toxicity_score,
                    "rule_triggered": m.rule_triggered,
                    "decision_reason": m.decision_reason,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
            "violations": [
                {
                    "id": v.id,
                    "type": v.violation_type,
                    "score": v.score,
                    "message_id": v.message_id,
                    "details_json": v.details_json,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in violations
            ],
            "moderation_actions": [
                {
                    "id": action.id,
                    "message_id": action.message_id,
                    "action": action.action,
                    "comment": action.comment,
                    "moderator": moderator_username,
                    "created_at": action.created_at.isoformat() if action.created_at else None,
                }
                for action, moderator_username in moderation_actions
            ],
        }
    )


@admin_bp.patch("/users/<int:user_id>")
@roles_required("admin")
def patch_user(user_id: int):
    payload = request.get_json(silent=True) or {}
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    if "role" in payload:
        role = str(payload["role"]).strip()
        if role not in {"user", "moderator", "admin"}:
            return jsonify({"error": "invalid_role"}), 400
        user.role = role

    if "is_blocked" in payload:
        user.is_blocked = bool(payload["is_blocked"])

    if "blocked_until" in payload:
        blocked_until = payload["blocked_until"]
        if blocked_until:
            try:
                if str(blocked_until).endswith("Z"):
                    blocked_until = str(blocked_until)[:-1] + "+00:00"
                user.blocked_until = datetime.fromisoformat(str(blocked_until))
            except ValueError:
                return jsonify({"error": "invalid_blocked_until"}), 400
        else:
            user.blocked_until = None

    if "warnings" in payload:
        try:
            user.warnings = max(0, int(payload["warnings"]))
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_warnings"}), 400

    if "rating_score" in payload:
        try:
            user.rating_score = min(1.0, max(0.0, float(payload["rating_score"])))
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_rating_score"}), 400

    if "shadow_ban" in payload:
        user.shadow_ban = bool(payload["shadow_ban"])

    db.session.commit()
    return jsonify({"ok": True, "user": user.to_public_dict()})
