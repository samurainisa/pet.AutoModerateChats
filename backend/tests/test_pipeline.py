from app.extensions import db
from app.models import Message, User


def test_pipeline_ok_message(app):
    with app.app_context():
        user = User(username="pipe_ok", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        result = pipeline.process_message(user=user, room="public", text="Привет всем")

        assert result["status"] == "ok"
        assert result["message"] is not None
        stored = db.session.get(Message, result["message"].id)
        assert stored is not None
        assert stored.status == "ok"


def test_pipeline_blocked_short_message_increments_warnings(app):
    with app.app_context():
        user = User(username="pipe_block", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        result = pipeline.process_message(user=user, room="public", text="a")

        assert result["status"] == "blocked"
        refreshed = db.session.get(User, user.id)
        assert refreshed.warnings == 1
