from datetime import datetime

from app.extensions import db
from app.models import Message, User
from app.services.rule_engine import RuleEngine


def test_rule_engine_blocks_short_text(app):
    with app.app_context():
        user = User(username="rule_short", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        engine = RuleEngine(db_session=db.session, config=app.config)
        result = engine.evaluate(user_id=user.id, text="a")
        assert result.action == "BLOCK"
        assert "length_lt_2" in result.reasons


def test_rule_engine_detects_flood(app):
    with app.app_context():
        user = User(username="rule_flood", password_hash="x", role="user")
        db.session.add(user)
        db.session.flush()

        for i in range(5):
            db.session.add(
                Message(
                    room="public",
                    user_id=user.id,
                    text_original=f"msg{i}",
                    text_normalized=f"msg{i}",
                    status="ok",
                    created_at=datetime.utcnow(),
                )
            )
        db.session.commit()

        engine = RuleEngine(db_session=db.session, config=app.config)
        result = engine.evaluate(user_id=user.id, text="new message")
        assert result.action == "BLOCK"
        assert "flood" in result.reasons


def test_rule_engine_warns_about_link(app):
    with app.app_context():
        user = User(username="rule_link", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        engine = RuleEngine(db_session=db.session, config=app.config)
        result = engine.evaluate(user_id=user.id, text="check https://example.com")
        assert result.action == "WARN"
        assert "link" in result.reasons

