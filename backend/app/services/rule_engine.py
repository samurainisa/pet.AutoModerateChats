import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import func

from ..models import Message, Setting


URL_RE = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
REPEATED_SYMBOLS_RE = re.compile(r"([a-zа-я0-9])\1{4,}", re.IGNORECASE)


@dataclass
class RuleResult:
    action: str = "ALLOW"  # ALLOW | WARN | BLOCK
    reasons: list[str] = field(default_factory=list)

    def block(self, reason: str) -> None:
        self.action = "BLOCK"
        self.reasons.append(reason)

    def warn(self, reason: str) -> None:
        if self.action != "BLOCK":
            self.action = "WARN"
        self.reasons.append(reason)


class RuleEngine:
    def __init__(self, db_session, config):
        self.db_session = db_session
        self.config = config
        stopwords = (config.get("STOPWORDS") or "").strip()
        self.stopwords = {token.strip().lower() for token in stopwords.split(",") if token.strip()}

    def _get_setting_int(self, key: str, fallback: int) -> int:
        row = self.db_session.get(Setting, key)
        if not row:
            return fallback
        try:
            return int(row.value)
        except (TypeError, ValueError):
            return fallback

    def evaluate(self, user_id: int, text: str) -> RuleResult:
        result = RuleResult()
        now = datetime.utcnow()

        if len(text) < 2:
            result.block("length_lt_2")

        flood_count = self._get_setting_int("flood_count", int(self.config.get("FLOOD_COUNT", 5)))
        flood_window = self._get_setting_int("flood_window", int(self.config.get("FLOOD_WINDOW", 30)))
        recent_from = now - timedelta(seconds=flood_window)
        recent_count = (
            self.db_session.query(func.count(Message.id))
            .filter(Message.user_id == user_id, Message.created_at >= recent_from)
            .scalar()
            or 0
        )
        if recent_count >= flood_count:
            result.block("flood")

        duplicate_window = self._get_setting_int("duplicate_window", int(self.config.get("DUPLICATE_WINDOW", 30)))
        duplicate_from = now - timedelta(seconds=duplicate_window)
        duplicate_exists = (
            self.db_session.query(Message.id)
            .filter(
                Message.user_id == user_id,
                Message.text_normalized == text,
                Message.created_at >= duplicate_from,
            )
            .first()
            is not None
        )
        if duplicate_exists:
            result.block("duplicate")

        if self.stopwords and any(word in text for word in self.stopwords):
            result.block("stopword")

        links = URL_RE.findall(text)
        if links:
            if len(links) > 2:
                result.block("too_many_links")
            else:
                result.warn("link")

        if REPEATED_SYMBOLS_RE.search(text):
            result.block("repeated_symbols")

        return result

