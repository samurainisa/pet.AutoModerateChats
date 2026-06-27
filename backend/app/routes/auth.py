from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User
from ..utils.auth import get_current_user
from ..utils.validators import validate_password, validate_username


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


try:
    import bcrypt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    bcrypt = None


def _hash_password(password: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return generate_password_hash(password)


def _check_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$2") and bcrypt is not None:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False
    return check_password_hash(password_hash, password)


def _issue_tokens(user: User) -> tuple[str, str]:
    claims = {"role": user.role, "username": user.username}
    access = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=claims)
    return access, refresh


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    email = (payload.get("email") or "").strip() or None

    username_error = validate_username(username)
    if username_error:
        return jsonify({"error": username_error}), 400

    password_error = validate_password(password)
    if password_error:
        return jsonify({"error": password_error}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username_taken"}), 409
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken"}), 409

    user = User(username=username, email=email, password_hash=_hash_password(password), role="user")
    db.session.add(user)
    db.session.commit()

    access_token, refresh_token = _issue_tokens(user)
    response = jsonify({"user": user.to_public_dict()})
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if user is None or not _check_password(password, user.password_hash):
        return jsonify({"error": "invalid_credentials"}), 401

    if user.is_temporarily_blocked():
        return (
            jsonify({"error": "user_blocked", "blocked_until": user.blocked_until.isoformat() if user.blocked_until else None}),
            403,
        )

    access_token, refresh_token = _issue_tokens(user)
    response = jsonify({"user": user.to_public_dict()})
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = get_current_user()
    if user is None:
        return jsonify({"error": "user_not_found"}), 404
    access_token, _refresh_token = _issue_tokens(user)
    response = jsonify({"ok": True})
    set_access_cookies(response, access_token)
    return response


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    claims = get_jwt()
    current_app.extensions["token_blocklist"].add(claims["jti"])

    refresh_cookie_name = current_app.config.get("JWT_REFRESH_COOKIE_NAME", "refresh_token_cookie")
    refresh_raw = request.cookies.get(refresh_cookie_name)
    if refresh_raw:
        try:
            refresh_claims = decode_token(refresh_raw, allow_expired=True)
            current_app.extensions["token_blocklist"].add(refresh_claims["jti"])
        except Exception:  # noqa: BLE001
            pass

    response = jsonify({"ok": True})
    unset_jwt_cookies(response)
    return response


@auth_bp.get("/me")
@jwt_required()
def me():
    user = get_current_user()
    if user is None:
        return jsonify({"error": "user_not_found"}), 404
    return jsonify({"user": user.to_public_dict()})
