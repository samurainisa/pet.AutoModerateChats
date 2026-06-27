from datetime import datetime

from app.extensions import db
from app.models import Message, MessageStatus, User, Violation


def test_moderation_queue_filters_and_not_found(app, client, login_user, create_user):
    with app.app_context():
        login_user("mod_queue", role="moderator")
        user = create_user("mod_queue_user")
        db.session.add_all(
            [
                Message(
                    room="public",
                    user_id=user.id,
                    text_original="h1",
                    text_normalized="h1",
                    status="hidden",
                    toxicity_score=0.41,
                ),
                Message(
                    room="public",
                    user_id=user.id,
                    text_original="h2",
                    text_normalized="h2",
                    status="hidden",
                    toxicity_score=0.8,
                ),
            ]
        )
        db.session.commit()

    queue_all = client.get("/api/moderation/queue")
    assert queue_all.status_code == 200
    assert len(queue_all.get_json()["items"]) == 2

    queue_filtered = client.get("/api/moderation/queue", query_string={"min_score": 0.7, "max_score": 0.9})
    assert queue_filtered.status_code == 200
    items = queue_filtered.get_json()["items"]
    assert len(items) == 1
    assert items[0]["score"] == 0.8

    missing_approve = client.post("/api/moderation/messages/99999/approve")
    assert missing_approve.status_code == 404

    missing_delete = client.post("/api/moderation/messages/99999/delete")
    assert missing_delete.status_code == 404

    missing_mute = client.post("/api/moderation/messages/99999/mute_user")
    assert missing_mute.status_code == 404


def test_moderation_delete_mute_profile_violations(app, client, login_user, create_user):
    with app.app_context():
        login_user("mod_actions", role="moderator")
        target = create_user("mod_target")
        target_id = target.id
        ok_message = Message(
            room="public",
            user_id=target_id,
            text_original="to delete",
            text_normalized="to delete",
            status="ok",
            toxicity_score=0.76,
        )
        blocked_message = Message(
            room="public",
            user_id=target_id,
            text_original="already blocked",
            text_normalized="already blocked",
            status="blocked",
            toxicity_score=0.95,
        )
        db.session.add_all([ok_message, blocked_message])
        db.session.flush()
        ok_id = ok_message.id
        blocked_id = blocked_message.id
        db.session.add(
            Violation(
                user_id=target_id,
                message_id=blocked_id,
                violation_type="toxicity",
                score=0.95,
                details_json="{}",
                created_at=datetime.utcnow(),
            )
        )
        db.session.commit()

    invalid_approve = client.post(f"/api/moderation/messages/{ok_id}/approve")
    assert invalid_approve.status_code == 400
    assert invalid_approve.get_json()["error"] == "invalid_status"

    invalid_delete = client.post(f"/api/moderation/messages/{blocked_id}/delete")
    assert invalid_delete.status_code == 400
    assert invalid_delete.get_json()["error"] == "invalid_status"

    delete_response = client.post(f"/api/moderation/messages/{ok_id}/delete", json={"comment": "remove"})
    assert delete_response.status_code == 200
    assert delete_response.get_json()["status"] == MessageStatus.DELETED.value

    with app.app_context():
        deleted = db.session.get(Message, ok_id)
        author = db.session.get(User, target_id)
        assert deleted.status == MessageStatus.DELETED.value
        assert author.warnings >= 1

    mute_response = client.post(f"/api/moderation/messages/{ok_id}/mute_user", json={"hours": 2})
    assert mute_response.status_code == 200
    assert mute_response.get_json()["user_id"] == target_id

    profile = client.get(f"/api/moderation/users/{target_id}")
    assert profile.status_code == 200
    payload = profile.get_json()
    assert payload["user"]["id"] == target_id
    assert len(payload["messages"]) >= 2
    assert len(payload["violations"]) >= 1

    profile_not_found = client.get("/api/moderation/users/99999")
    assert profile_not_found.status_code == 404

    violations = client.get("/api/moderation/violations", query_string={"limit": 1})
    assert violations.status_code == 200
    assert len(violations.get_json()["items"]) == 1

