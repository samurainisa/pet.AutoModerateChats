from app.extensions import db
from app.models import Message, Setting, User
from app.services.decision_engine import DecisionEngine
from app.services.ml_classifier import ToxicityClassifier
from app.services.rating_service import RatingService
from app.services.rule_engine import RuleEngine, RuleResult


def test_decision_engine_shadow_ban_and_invalid_setting_fallback(app):
    with app.app_context():
        low_row = db.session.get(Setting, "low_threshold")
        high_row = db.session.get(Setting, "high_threshold")
        low_row.value = "not-a-float"
        high_row.value = "0.8"
        user = User(username="decision_shadow", password_hash="x", role="user", shadow_ban=True, rating_score=0.9)
        db.session.add(user)
        db.session.commit()

        engine = DecisionEngine(db_session=db.session, config=app.config)
        result = engine.decide(user=user, rule_result=RuleResult(action="ALLOW"), ml_result={"aggregate": 0.1})
        assert result.status == "hidden"
        assert result.reason == "shadow_ban_or_high_rating"


def test_decision_engine_warn_reason_and_rating_adjust(app):
    with app.app_context():
        user = User(username="decision_warn", password_hash="x", role="user", rating_score=0.7)
        db.session.add(user)
        db.session.commit()

        engine = DecisionEngine(db_session=db.session, config=app.config)
        result = engine.decide(
            user=user,
            rule_result=RuleResult(action="WARN", reasons=["link"]),
            ml_result={"aggregate": 0.38},
        )
        assert result.status in {"ok", "hidden"}
        assert "rule_warn:link" in result.reason
        assert "thresholds:" in result.reason


def test_rule_engine_stopwords_links_repeats_and_setting_fallback(app):
    with app.app_context():
        user = User(username="rule_full", password_hash="x", role="user")
        db.session.add(user)
        db.session.flush()
        flood_row = db.session.get(Setting, "flood_count")
        flood_row.value = "bad-value"
        db.session.commit()

        engine = RuleEngine(db_session=db.session, config={**app.config, "STOPWORDS": "badword"})
        result = engine.evaluate(
            user_id=user.id,
            text="badword https://a.com https://b.com https://c.com aaaaaaa",
        )
        assert result.action == "BLOCK"
        assert "stopword" in result.reasons
        assert "too_many_links" in result.reasons
        assert "repeated_symbols" in result.reasons


def test_rating_service_shadow_and_temp_block_from_setting(app):
    with app.app_context():
        row = db.session.get(Setting, "temp_block_hours")
        row.value = "2"
        user = User(username="rating_user", password_hash="x", role="user", warnings=2, rating_score=0.9)
        db.session.add(user)
        db.session.commit()

        service = RatingService(db_session=db.session, config=app.config)
        snapshot = service.update_after_message(user=user, last_toxicity_score=1.0, message_status="blocked")
        assert snapshot["warnings"] == 3
        assert snapshot["is_blocked"] is True
        assert snapshot["shadow_ban"] is True
        assert snapshot["blocked_until"] is not None


def test_ml_classifier_fallback_and_error_branches(monkeypatch):
    import types

    fake_transformers = types.ModuleType("transformers")

    def _failing_pipeline(*args, **kwargs):
        raise RuntimeError("model load failed")

    fake_transformers.pipeline = _failing_pipeline
    monkeypatch.setitem(__import__("sys").modules, "transformers", fake_transformers)

    classifier = ToxicityClassifier(model_name="some-unavailable-model-name")
    fallback = classifier.score("text")
    assert fallback["fallback"] is True

    classifier._is_ready = True
    classifier._pipe = lambda _text: [[{"label": "non-toxic", "score": 0.2}, {"label": "insult", "score": 0.8}]]
    scored = classifier.score("hello")
    assert scored["fallback"] is False
    assert scored["aggregate"] == 0.8
    assert scored["labels"]["insult"] == 0.8

    def _broken(_text):
        raise RuntimeError("boom")

    classifier._pipe = _broken
    errored = classifier.score("hello")
    assert errored["fallback"] is True
    assert "error" in errored


def test_rule_engine_duplicate_branch(app):
    with app.app_context():
        user = User(username="rule_duplicate", password_hash="x", role="user")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Message(
                room="public",
                user_id=user.id,
                text_original="hello",
                text_normalized="hello",
                status="ok",
            )
        )
        db.session.commit()

        engine = RuleEngine(db_session=db.session, config=app.config)
        result = engine.evaluate(user_id=user.id, text="hello")
        assert "duplicate" in result.reasons
