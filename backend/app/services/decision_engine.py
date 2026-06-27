from dataclasses import dataclass

from ..models import Setting


@dataclass
class DecisionResult:
    status: str
    reason: str
    score: float
    low_threshold: float
    high_threshold: float


class DecisionEngine:
    def __init__(self, db_session, config):
        self.db_session = db_session
        self.config = config

    def _get_setting_float(self, key: str, fallback: float) -> float:
        row = self.db_session.get(Setting, key)
        if not row:
            return fallback
        try:
            return float(row.value)
        except (TypeError, ValueError):
            return fallback

    def decide(self, user, rule_result, ml_result) -> DecisionResult:
        if rule_result.action == "BLOCK":
            return DecisionResult(
                status="blocked",
                reason="rule_block:" + ",".join(rule_result.reasons),
                score=float(ml_result.get("aggregate", 0.0)),
                low_threshold=self._get_setting_float("low_threshold", float(self.config.get("LOW_THRESHOLD", 0.4))),
                high_threshold=self._get_setting_float("high_threshold", float(self.config.get("HIGH_THRESHOLD", 0.75))),
            )

        low = self._get_setting_float("low_threshold", float(self.config.get("LOW_THRESHOLD", 0.4)))
        high = self._get_setting_float("high_threshold", float(self.config.get("HIGH_THRESHOLD", 0.75)))
        score = float(ml_result.get("aggregate", 0.0))

        if float(user.rating_score or 0.0) > 0.6:
            low = max(0.0, low - 0.05)
            high = max(low + 0.05, high - 0.05)

        if bool(user.shadow_ban) or float(user.rating_score or 0.0) > 0.8:
            return DecisionResult(
                status="hidden",
                reason="shadow_ban_or_high_rating",
                score=score,
                low_threshold=low,
                high_threshold=high,
            )

        if score < low:
            status = "ok"
        elif score < high:
            status = "hidden"
        else:
            status = "blocked"

        reasons = []
        if rule_result.action == "WARN":
            reasons.append("rule_warn:" + ",".join(rule_result.reasons))
        reasons.append(f"score:{score:.4f}")
        reasons.append(f"thresholds:{low:.2f}/{high:.2f}")

        return DecisionResult(
            status=status,
            reason=";".join(reasons),
            score=score,
            low_threshold=low,
            high_threshold=high,
        )

