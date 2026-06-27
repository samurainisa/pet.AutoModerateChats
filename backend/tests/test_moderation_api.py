from app.extensions import db
from app.models import Message, User
from werkzeug.security import generate_password_hash


def _login(client, username: str, password: str = "password"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_moderation_queue_and_approve(app, client):
    with app.app_context():
        moderator = User(username="mod1", password_hash=generate_password_hash("password"), role="moderator")
        user = User(username="user1", password_hash=generate_password_hash("password"), role="user")
        db.session.add(moderator)
        db.session.add(user)
        db.session.flush()

        hidden_message = Message(
            room="public",
            user_id=user.id,
            text_original="подозрительный текст",
            text_normalized="подозрительный текст",
            status="hidden",
            toxicity_score=0.55,
        )
        db.session.add(hidden_message)
        db.session.commit()

        message_id = hidden_message.id

    login_response = _login(client, "mod1")
    assert login_response.status_code == 200

    queue_response = client.get("/api/moderation/queue")
    assert queue_response.status_code == 200
    assert len(queue_response.get_json()["items"]) == 1

    approve_response = client.post(f"/api/moderation/messages/{message_id}/approve", json={"comment": "ok"})
    assert approve_response.status_code == 200
    assert approve_response.get_json()["status"] == "approved_manual"
