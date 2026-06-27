from flask import current_app
from flask_jwt_extended import verify_jwt_in_request
from flask_socketio import emit, join_room, leave_room

from ..utils.auth import get_current_user
from ..utils.validators import validate_message_text


def register_chat_namespace(socketio):
    namespace = "/chat"

    @socketio.on("connect", namespace=namespace)
    def on_connect():
        try:
            verify_jwt_in_request()
        except Exception:  # noqa: BLE001
            return False

        user = get_current_user()
        if user is None:
            return False

        join_room("public")
        if user.role in {"moderator", "admin"}:
            join_room("moderators")
        emit("connected", {"ok": True, "user": user.username})

    @socketio.on("join_room", namespace=namespace)
    def on_join_room(data):
        room = (data or {}).get("room", "public")
        if room != "public":
            emit("error", {"error": "room_not_allowed"})
            return
        join_room(room)
        emit("joined_room", {"room": room})

    @socketio.on("leave_room", namespace=namespace)
    def on_leave_room(data):
        room = (data or {}).get("room", "public")
        leave_room(room)
        emit("left_room", {"room": room})

    @socketio.on("send_message", namespace=namespace)
    def on_send_message(data):
        try:
            verify_jwt_in_request()
        except Exception:  # noqa: BLE001
            emit("message_blocked", {"reason": "unauthorized", "score": 0.0, "rule": "auth"})
            return

        user = get_current_user()
        if user is None:
            emit("message_blocked", {"reason": "user_not_found", "score": 0.0, "rule": "auth"})
            return

        room = (data or {}).get("room", "public")
        if room != "public":
            emit("message_blocked", {"reason": "room_not_allowed", "score": 0.0, "rule": "room"})
            return

        text = (data or {}).get("text", "")
        error = validate_message_text(text, max_length=int(current_app.config.get("MESSAGE_MAX_LENGTH", 512)))
        if error:
            emit("message_blocked", {"reason": error, "score": 0.0, "rule": "validation"})
            return

        pipeline = current_app.extensions["moderation_pipeline"]
        result = pipeline.process_message(user=user, room=room, text=text)

        message = result.get("message")
        status = result["status"]
        score = float(result.get("score", 0.0) or 0.0)
        reason = result.get("reason")
        rule = result.get("rule")

        if status in {"ok", "approved_manual"} and message is not None:
            emit("new_message", message.to_event_dict(), namespace=namespace, room=room)
            return

        if status == "hidden" and message is not None:
            emit(
                "message_hidden",
                {
                    "id": message.id,
                    "author": user.username,
                    "text": message.text_original,
                    "score": score,
                    "reason": reason,
                    "rule": rule,
                },
                namespace=namespace,
                room="moderators",
            )
            emit("message_updated", {"id": message.id, "status": "hidden"}, namespace=namespace)
            return

        emit("message_blocked", {"reason": reason, "score": score, "rule": rule}, namespace=namespace)

