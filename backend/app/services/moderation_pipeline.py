import json
from datetime import datetime

from ..models import Message, Violation
from .decision_engine import DecisionEngine
from .normalizer import TextNormalizer
from .rating_service import RatingService
from .rule_engine import RuleEngine


class ModerationPipeline:
    def __init__(self, db_session, config, classifier, audit_service):
        self.db_session = db_session
        self.config = config
        self.classifier = classifier
        self.audit = audit_service
        self.normalizer = TextNormalizer(max_length=int(config.get("MESSAGE_MAX_LENGTH", 512)))
        self.rule_engine = RuleEngine(db_session=db_session, config=config)
        self.decision_engine = DecisionEngine(db_session=db_session, config=config)
        self.rating_service = RatingService(db_session=db_session, config=config)

    def process_message(self, user, room: str, text: str) -> dict:
        if user.is_temporarily_blocked():
            self.audit.log(
                user_id=user.id,
                message_id=None,
                stage="access",
                action="reject_blocked_user",
                status="blocked",
                details={"blocked_until": user.blocked_until.isoformat() if user.blocked_until else None},
            )
            return {
                "status": "blocked",
                "reason": "user_blocked",
                "score": 0.0,
                "message": None,
                "rule": "user_blocked",
            }

        normalized = self.normalizer.normalize(text)
        self.audit.log(
            user_id=user.id,
            message_id=None,
            stage="normalize",
            action="normalize_message",
            status="ok",
            details={"normalized": normalized},
        )

        rule_result = self.rule_engine.evaluate(user_id=user.id, text=normalized)
        self.audit.log(
            user_id=user.id,
            message_id=None,
            stage="rule_engine",
            action="evaluate",
            status=rule_result.action,
            details={"reasons": rule_result.reasons},
        )

        ml_result = {"aggregate": 0.0, "labels": {}, "fallback": False}
        if rule_result.action != "BLOCK":
            ml_result = self.classifier.score(normalized)
            self.audit.log(
                user_id=user.id,
                message_id=None,
                stage="ml",
                action="score",
                status="fallback" if ml_result.get("fallback") else "ok",
                details={"aggregate": ml_result.get("aggregate"), "labels": ml_result.get("labels", {})},
            )

        decision = self.decision_engine.decide(user=user, rule_result=rule_result, ml_result=ml_result)

        message = Message(
            room=room,
            user_id=user.id,
            text_original=text,
            text_normalized=normalized,
            status=decision.status,
            toxicity_score=decision.score,
            ml_labels_json=json.dumps(ml_result.get("labels", {}), ensure_ascii=False),
            rule_triggered=",".join(rule_result.reasons) if rule_result.reasons else None,
            decision_reason=decision.reason,
            created_at=datetime.utcnow(),
        )
        self.db_session.add(message)
        self.db_session.flush()

        violation_types = []
        if decision.status in {"blocked", "hidden"}:
            if "flood" in rule_result.reasons:
                violation_types.append("flood")
            if "duplicate" in rule_result.reasons:
                violation_types.append("duplicate")
            if "stopword" in rule_result.reasons:
                violation_types.append("stopword")
            if "link" in rule_result.reasons or "too_many_links" in rule_result.reasons:
                violation_types.append("link")
            if decision.score >= decision.low_threshold:
                violation_types.append("toxicity")
            if not violation_types:
                violation_types.append("rule")

        for violation_type in violation_types:
            violation = Violation(
                user_id=user.id,
                message_id=message.id,
                violation_type=violation_type,
                score=decision.score,
                details_json=json.dumps(
                    {
                        "rule_reasons": rule_result.reasons,
                        "decision_reason": decision.reason,
                        "labels": ml_result.get("labels", {}),
                    },
                    ensure_ascii=False,
                ),
            )
            self.db_session.add(violation)

        rating_snapshot = self.rating_service.update_after_message(
            user=user, last_toxicity_score=decision.score, message_status=decision.status
        )
        self.db_session.add(user)
        self.db_session.commit()

        self.audit.log(
            user_id=user.id,
            message_id=message.id,
            stage="decision",
            action="finalize",
            status=decision.status,
            details={
                "reason": decision.reason,
                "score": decision.score,
                "rule_reasons": rule_result.reasons,
                "rating": rating_snapshot,
            },
        )

        return {
            "status": decision.status,
            "reason": decision.reason,
            "score": decision.score,
            "rule": ",".join(rule_result.reasons) if rule_result.reasons else None,
            "message": message,
            "labels": ml_result.get("labels", {}),
        }

