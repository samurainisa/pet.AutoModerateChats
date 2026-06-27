from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User


class SeedUsersConfig(TestConfig):
    SEED_DEFAULT_USERS = True
    DEMO_USERS_PASSWORD = "seed-pass-123"
    DEMO_USER_USERNAME = "seed_user"
    DEMO_MODERATOR_USERNAME = "seed_moderator"
    DEMO_ADMIN_USERNAME = "seed_admin"


def test_default_users_are_seeded_and_can_login():
    app = create_app(SeedUsersConfig)
    client = app.test_client()

    expected = {
        "seed_user": "user",
        "seed_moderator": "moderator",
        "seed_admin": "admin",
    }

    with app.app_context():
        for username, role in expected.items():
            user = User.query.filter_by(username=username).first()
            assert user is not None
            assert user.role == role
            assert user.is_blocked is False
            assert user.shadow_ban is False
            assert user.warnings == 0
            assert float(user.rating_score or 0) == 0.0

    for username in expected:
        response = client.post("/api/auth/login", json={"username": username, "password": "seed-pass-123"})
        assert response.status_code == 200
        assert response.get_json()["user"]["username"] == username

    with app.app_context():
        db.session.remove()

