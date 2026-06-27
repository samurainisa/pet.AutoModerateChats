from app.utils.validators import validate_message_text, validate_password, validate_username


def test_validate_username():
    assert validate_username("") == "username_required"
    assert validate_username("ab") == "username_invalid"
    assert validate_username("valid_user_123") is None


def test_validate_password():
    assert validate_password("") == "password_required"
    assert validate_password("123") == "password_too_short"
    assert validate_password("123456") is None


def test_validate_message_text():
    assert validate_message_text(None) == "text_required"
    assert validate_message_text("   ") == "text_required"
    assert validate_message_text("x" * 513) == "text_too_long"
    assert validate_message_text("ok") is None

