from datetime import datetime, timedelta

from ..models import Setting


class RatingService:
    def __init__(self, db_session, config):
        self.db_session = db_session
        self.config = config

    def _get_setting_int(self, key: str, fallback: int) -> int:
        row = self.db_session.get(Setting, key)
        if not row:
            return fallback
        try:
            return int(row.value)
        except (TypeError, ValueError):
            return fallback

    def update_after_message(self, user, last_toxicity_score: float, message_status: str) -> dict:
        previous_rating = float(user.rating_score or 0.0)
        new_rating = 0.7 * previous_rating + 0.3 * float(last_toxicity_score or 0.0)
        user.rating_score = min(1.0, max(0.0, new_rating))

        if message_status in {"blocked", "deleted"}:
            user.warnings = int(user.warnings or 0) + 1

        if user.rating_score > 0.8:
            user.shadow_ban = True

        temp_block_hours = self._get_setting_int("temp_block_hours", int(self.config.get("TEMP_BLOCK_HOURS", 24)))
        if int(user.warnings or 0) >= 3:
            user.is_blocked = True
            user.blocked_until = datetime.utcnow() + timedelta(hours=temp_block_hours)

        return {
            "rating_score": float(user.rating_score),
            "warnings": int(user.warnings or 0),
            "is_blocked": bool(user.is_blocked),
            "blocked_until": user.blocked_until.isoformat() if user.blocked_until else None,
            "shadow_ban": bool(user.shadow_ban),
        }

