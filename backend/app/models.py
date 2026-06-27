from datetime import datetime
from enum import Enum

from sqlalchemy import func

from .extensions import db


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class MessageStatus(str, Enum):
    PENDING = "pending"
    OK = "ok"
    HIDDEN = "hidden"
    BLOCKED = "blocked"
    DELETED = "deleted"
    APPROVED_MANUAL = "approved_manual"


class ViolationType(str, Enum):
    SPAM = "spam"
    FLOOD = "flood"
    DUPLICATE = "duplicate"
    STOPWORD = "stopword"
    TOXICITY = "toxicity"
    LINK = "link"
    ADMIN_ACTION = "admin_action"
    RULE = "rule"


class ModerationActionType(str, Enum):
    APPROVE = "approve"
    DELETE = "delete"
    MUTE_USER = "mute_user"
    UNMUTE_USER = "unmute_user"


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(256), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default=UserRole.USER.value)
    rating_score = db.Column(db.Float, nullable=False, default=0.0)
    warnings = db.Column(db.Integer, nullable=False, default=0)
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)
    blocked_until = db.Column(db.DateTime, nullable=True)
    shadow_ban = db.Column(db.Boolean, nullable=False, default=False)

    messages = db.relationship("Message", back_populates="author", foreign_keys="Message.user_id")

    def is_temporarily_blocked(self) -> bool:
        if not self.is_blocked:
            return False
        if self.blocked_until is None:
            return True
        return self.blocked_until > datetime.utcnow()

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "rating_score": round(float(self.rating_score or 0), 4),
            "warnings": int(self.warnings or 0),
            "is_blocked": bool(self.is_blocked),
            "blocked_until": self.blocked_until.isoformat() if self.blocked_until else None,
            "shadow_ban": bool(self.shadow_ban),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(64), nullable=False, default="public", index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text_original = db.Column(db.Text, nullable=False)
    text_normalized = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(24), nullable=False, default=MessageStatus.PENDING.value, index=True)
    toxicity_score = db.Column(db.Float, nullable=True)
    ml_labels_json = db.Column(db.Text, nullable=True)
    rule_triggered = db.Column(db.Text, nullable=True)
    decision_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    author = db.relationship("User", foreign_keys=[user_id], back_populates="messages")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    violations = db.relationship("Violation", back_populates="message", cascade="all, delete-orphan")

    def to_event_dict(self) -> dict:
        return {
            "id": self.id,
            "room": self.room,
            "author": self.author.username if self.author else None,
            "text": self.text_original,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "score": self.toxicity_score,
        }


class Violation(db.Model):
    __tablename__ = "violations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False, index=True)
    violation_type = db.Column(db.String(32), nullable=False, index=True)
    score = db.Column(db.Float, nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)

    user = db.relationship("User")
    message = db.relationship("Message", back_populates="violations")


class ModerationAction(db.Model):
    __tablename__ = "moderation_actions"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False, index=True)
    moderator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(32), nullable=False, index=True)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)

    message = db.relationship("Message")
    moderator = db.relationship("User")


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

