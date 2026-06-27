from __future__ import annotations

import re


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def validate_username(username: str) -> str | None:
    if not username:
        return "username_required"
    if not USERNAME_RE.match(username):
        return "username_invalid"
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "password_required"
    if len(password) < 6:
        return "password_too_short"
    return None


def validate_message_text(text: str, max_length: int = 512) -> str | None:
    if text is None:
        return "text_required"
    if len(text.strip()) == 0:
        return "text_required"
    if len(text) > max_length:
        return "text_too_long"
    return None

