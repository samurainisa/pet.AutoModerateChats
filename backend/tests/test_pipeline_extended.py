from datetime import datetime, timedelta

from app.extensions import db
from app.models import Message, User, Violation


def test_pipeline_blocked_user_early_return(app):
    with app.app_context():
        user = User(
            username="pipe_blocked_user",
            password_hash="x",
            role="user",
            is_blocked=True,
            blocked_until=datetime.utcnow() + timedelta(hours=1),
        )
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        result = pipeline.process_message(user=user, room="public", text="hello")

        assert result["status"] == "blocked"
        assert result["reason"] == "user_blocked"
        assert result["message"] is None
        assert Message.query.count() == 0


def test_pipeline_hidden_for_shadow_banned_user(app):
    with app.app_context():
        user = User(username="pipe_shadow", password_hash="x", role="user", shadow_ban=True)
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        result = pipeline.process_message(user=user, room="public", text="normal message")

        assert result["status"] == "hidden"
        assert result["message"] is not None
        violations = Violation.query.filter_by(message_id=result["message"].id).all()
        assert len(violations) >= 1


def test_pipeline_rule_block_does_not_call_ml(app):
    class ExplodingClassifier:
        def score(self, text: str):  # pragma: no cover - should not execute
            raise RuntimeError(f"ML must not be called for block: {text}")

    with app.app_context():
        user = User(username="pipe_rule_no_ml", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        pipeline.classifier = ExplodingClassifier()
        result = pipeline.process_message(user=user, room="public", text="a")
        assert result["status"] == "blocked"
        assert "length_lt_2" in (result["rule"] or "")


def test_pipeline_creates_toxicity_violation_and_updates_block(app):
    class HighScoreClassifier:
        def score(self, _text: str):
            return {"aggregate": 0.95, "labels": {"insult": 0.95}, "fallback": False}

    with app.app_context():
        user = User(username="pipe_toxic", password_hash="x", role="user", warnings=2)
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        pipeline.classifier = HighScoreClassifier()
        result = pipeline.process_message(user=user, room="public", text="агрессивный текст")

        assert result["status"] == "blocked"
        stored_user = db.session.get(User, user.id)
        assert stored_user.warnings == 3
        assert stored_user.is_blocked is True
        assert stored_user.blocked_until is not None

        violations = Violation.query.filter_by(message_id=result["message"].id).all()
        types = {item.violation_type for item in violations}
        assert "toxicity" in types


def test_pipeline_hidden_by_mid_toxicity_score(app):
    class MidScoreClassifier:
        def score(self, _text: str):
            return {"aggregate": 0.5, "labels": {"insult": 0.5}, "fallback": False}

    with app.app_context():
        user = User(username="pipe_mid_score", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        pipeline.classifier = MidScoreClassifier()
        result = pipeline.process_message(user=user, room="public", text="граничный кейс")

        assert result["status"] == "hidden"
        violations = Violation.query.filter_by(message_id=result["message"].id).all()
        assert any(v.violation_type == "toxicity" for v in violations)


def test_pipeline_duplicate_violation(app):
    with app.app_context():
        user = User(username="pipe_dup", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        pipeline = app.extensions["moderation_pipeline"]
        first = pipeline.process_message(user=user, room="public", text="одинаковый текст")
        second = pipeline.process_message(user=user, room="public", text="одинаковый текст")

        assert first["status"] == "ok"
        assert second["status"] == "blocked"
        assert "duplicate" in (second["rule"] or "")

        violations = Violation.query.filter_by(message_id=second["message"].id).all()
        assert any(v.violation_type == "duplicate" for v in violations)
