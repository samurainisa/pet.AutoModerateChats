from app.extensions import db
from app.models import User
from app.services.decision_engine import DecisionEngine
from app.services.rule_engine import RuleResult


def test_decision_engine_thresholds(app):
    with app.app_context():
        user = User(username="u1", password_hash="x", role="user", rating_score=0.0)
        db.session.add(user)
        db.session.commit()

        engine = DecisionEngine(db_session=db.session, config=app.config)

        result_ok = engine.decide(user=user, rule_result=RuleResult(action="ALLOW"), ml_result={"aggregate": 0.1})
        assert result_ok.status == "ok"

        result_hidden = engine.decide(user=user, rule_result=RuleResult(action="ALLOW"), ml_result={"aggregate": 0.5})
        assert result_hidden.status == "hidden"

        result_block = engine.decide(user=user, rule_result=RuleResult(action="ALLOW"), ml_result={"aggregate": 0.9})
        assert result_block.status == "blocked"


def test_decision_engine_rule_block_priority(app):
    with app.app_context():
        user = User(username="u2", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()

        engine = DecisionEngine(db_session=db.session, config=app.config)
        rules = RuleResult(action="BLOCK", reasons=["stopword"])
        result = engine.decide(user=user, rule_result=rules, ml_result={"aggregate": 0.01})
        assert result.status == "blocked"
        assert "rule_block" in result.reason

