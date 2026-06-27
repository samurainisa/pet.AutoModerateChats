import json
import logging
from datetime import datetime
from typing import Any


class AuditService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log(self, *, user_id: int | None, message_id: int | None, stage: str, action: str, status: str, details: dict[str, Any] | None = None) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "message_id": message_id,
            "stage": stage,
            "action": action,
            "status": status,
            "details": details or {},
        }
        self.logger.info("AUDIT %s", json.dumps(payload, ensure_ascii=False))

