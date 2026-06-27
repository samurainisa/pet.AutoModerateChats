from datetime import datetime, timedelta

from app.extensions import db
from app.models import User


def test_register_validation_and_duplicates(client):
    bad_username = client.post("/api/auth/register", json={"username": "a", "password": "password"})
    assert bad_username.status_code == 400
    assert bad_username.get_json()["error"] == "username_invalid"

    bad_password = client.post("/api/auth/register", json={"username": "validuser", "password": "123"})
    assert bad_password.status_code == 400
    assert bad_password.get_json()["error"] == "password_too_short"

    ok = client.post("/api/auth/register", json={"username": "dup_user", "password": "password", "email": "dup@ex.com"})
    assert ok.status_code == 201

    dup_username = client.post("/api/auth/register", json={"username": "dup_user", "password": "password"})
    assert dup_username.status_code == 409
    assert dup_username.get_json()["error"] == "username_taken"

    dup_email = client.post("/api/auth/register", json={"username": "dup_user2", "password": "password", "email": "dup@ex.com"})
    assert dup_email.status_code == 409
    assert dup_email.get_json()["error"] == "email_taken"


def test_login_errors_and_blocked_user(app, client, create_user):
    bad_login = client.post("/api/auth/login", json={"username": "nope", "password": "password"})
    assert bad_login.status_code == 401
    assert bad_login.get_json()["error"] == "invalid_credentials"

    with app.app_context():
        blocked = create_user(
            "blocked_user",
            is_blocked=True,
            blocked_until=datetime.utcnow() + timedelta(hours=1),
        )
        blocked_id = blocked.id

    blocked_login = client.post("/api/auth/login", json={"username": "blocked_user", "password": "password"})
    assert blocked_login.status_code == 403
    assert blocked_login.get_json()["error"] == "user_blocked"
    assert blocked_login.get_json()["blocked_until"] is not None

    with app.app_context():
        user = db.session.get(User, blocked_id)
        assert user is not None


def test_refresh_logout_and_me_branches(app, client, create_user, monkeypatch):
    register = client.post("/api/auth/register", json={"username": "refresh_user", "password": "password"})
    assert register.status_code == 201

    refresh = client.post("/api/auth/refresh")
    assert refresh.status_code == 200
    assert refresh.get_json()["ok"] is True

    me = client.get("/api/auth/me")
    assert me.status_code == 200

    monkeypatch.setattr("app.routes.auth.get_current_user", lambda: None)
    refresh_missing_user = client.post("/api/auth/refresh")
    assert refresh_missing_user.status_code == 404
    assert refresh_missing_user.get_json()["error"] == "user_not_found"

    # Ensure logout handles malformed refresh cookie (decode_token exception branch).
    replacement = create_user("refresh_user_2")
    login_again = client.post("/api/auth/login", json={"username": "refresh_user_2", "password": "password"})
    assert login_again.status_code == 200

    client.set_cookie("refresh_token_cookie", "malformed-token")
    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.get_json()["ok"] is True

    me_unauthorized = client.get("/api/auth/me")
    assert me_unauthorized.status_code == 401


def test_revoke_endpoint_revokes_current_access_token(client):
    register = client.post("/api/auth/register", json={"username": "revoke_user", "password": "password"})
    assert register.status_code == 201

    revoke = client.post("/api/auth/revoke")
    assert revoke.status_code == 200
    assert revoke.get_json()["ok"] is True

    me_after_revoke = client.get("/api/auth/me")
    assert me_after_revoke.status_code == 401
