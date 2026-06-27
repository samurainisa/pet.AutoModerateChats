from datetime import datetime, timedelta

from app.extensions import db
from app.models import Message


def test_messages_endpoint_requires_auth(client):
    response = client.get("/api/messages")
    assert response.status_code == 401


def test_messages_returns_visible_and_own_hidden(app, client, login_user, create_user):
    with app.app_context():
        user = login_user("messages_user")
        other = create_user("messages_other")

        now = datetime.utcnow()
        db.session.add_all(
            [
                Message(
                    room="public",
                    user_id=other.id,
                    text_original="visible_ok",
                    text_normalized="visible_ok",
                    status="ok",
                    created_at=now - timedelta(seconds=3),
                ),
                Message(
                    room="public",
                    user_id=other.id,
                    text_original="visible_approved",
                    text_normalized="visible_approved",
                    status="approved_manual",
                    created_at=now - timedelta(seconds=2),
                ),
                Message(
                    room="public",
                    user_id=other.id,
                    text_original="hidden_other",
                    text_normalized="hidden_other",
                    status="hidden",
                    created_at=now - timedelta(seconds=1),
                ),
                Message(
                    room="public",
                    user_id=user.id,
                    text_original="hidden_own",
                    text_normalized="hidden_own",
                    status="hidden",
                    created_at=now,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/api/messages", query_string={"room": "public", "limit": 100})
    assert response.status_code == 200
    payload = response.get_json()
    texts = {item["text"] for item in payload["items"]}

    assert "visible_ok" in texts
    assert "visible_approved" in texts
    assert "hidden_own" in texts
    assert "hidden_other" not in texts
    assert payload["next_before"] is not None


def test_messages_before_and_invalid_before(app, client, login_user, create_user):
    with app.app_context():
        user = login_user("messages_before")
        other = create_user("messages_before_other")
        older = datetime.utcnow() - timedelta(minutes=2)
        newer = datetime.utcnow() - timedelta(seconds=10)

        db.session.add_all(
            [
                Message(
                    room="public",
                    user_id=other.id,
                    text_original="older_message",
                    text_normalized="older_message",
                    status="ok",
                    created_at=older,
                ),
                Message(
                    room="public",
                    user_id=other.id,
                    text_original="newer_message",
                    text_normalized="newer_message",
                    status="ok",
                    created_at=newer,
                ),
                Message(
                    room="public",
                    user_id=user.id,
                    text_original="own_hidden",
                    text_normalized="own_hidden",
                    status="hidden",
                    created_at=newer,
                ),
            ]
        )
        db.session.commit()

    invalid_before = client.get("/api/messages", query_string={"before": "not-a-date"})
    assert invalid_before.status_code == 200
    assert len(invalid_before.get_json()["items"]) == 3

    before_value = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z"
    filtered = client.get("/api/messages", query_string={"before": before_value, "limit": 50})
    assert filtered.status_code == 200
    items = filtered.get_json()["items"]
    assert len(items) == 1
    assert items[0]["text"] == "older_message"

