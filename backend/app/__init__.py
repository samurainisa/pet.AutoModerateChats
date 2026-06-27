from flask import Flask
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash

from .config import Config
from .extensions import cors, db, jwt, migrate, socketio
from .models import Setting, User
from .services.audit_service import AuditService
from .services.ml_classifier import get_classifier
from .services.moderation_pipeline import ModerationPipeline


def _seed_settings(app: Flask) -> None:
    defaults = {
        "low_threshold": str(app.config["LOW_THRESHOLD"]),
        "high_threshold": str(app.config["HIGH_THRESHOLD"]),
        "flood_count": str(app.config["FLOOD_COUNT"]),
        "flood_window": str(app.config["FLOOD_WINDOW"]),
        "duplicate_window": str(app.config["DUPLICATE_WINDOW"]),
        "temp_block_hours": str(app.config["TEMP_BLOCK_HOURS"]),
    }
    for key, value in defaults.items():
        if db.session.get(Setting, key) is None:
            db.session.add(Setting(key=key, value=value))
    db.session.commit()


def _seed_default_users(app: Flask) -> None:
    if not app.config.get("SEED_DEFAULT_USERS", True):
        return

    demo_password = str(app.config.get("DEMO_USERS_PASSWORD", "demo12345"))
    demo_hash = generate_password_hash(demo_password)
    defaults = [
        {"username": str(app.config.get("DEMO_USER_USERNAME", "demo_user")), "role": "user"},
        {"username": str(app.config.get("DEMO_MODERATOR_USERNAME", "demo_moderator")), "role": "moderator"},
        {"username": str(app.config.get("DEMO_ADMIN_USERNAME", "demo_admin")), "role": "admin"},
    ]

    for item in defaults:
        user = User.query.filter_by(username=item["username"]).first()
        if user is None:
            user = User(
                username=item["username"],
                password_hash=demo_hash,
                role=item["role"],
                rating_score=0.0,
                warnings=0,
                is_blocked=False,
                blocked_until=None,
                shadow_ban=False,
            )
            db.session.add(user)
            continue

        user.role = item["role"]
        user.password_hash = demo_hash
        user.rating_score = 0.0
        user.warnings = 0
        user.is_blocked = False
        user.blocked_until = None
        user.shadow_ban = False

    db.session.commit()


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["CORS_ORIGINS"],
        async_mode=app.config.get("SOCKETIO_ASYNC_MODE", "threading"),
    )
    app.extensions["token_blocklist"] = set()

    classifier = get_classifier(app.config["ML_MODEL"])
    audit_service = AuditService(app.logger)
    app.extensions["moderation_pipeline"] = ModerationPipeline(
        db_session=db.session,
        config=app.config,
        classifier=classifier,
        audit_service=audit_service,
    )

    @jwt.token_in_blocklist_loader
    def _is_token_revoked(_jwt_header, jwt_payload):
        blocklist = app.extensions.get("token_blocklist", set())
        return jwt_payload["jti"] in blocklist

    @jwt.user_lookup_loader
    def _load_user(_jwt_header, jwt_payload):
        from .models import User

        identity = jwt_payload["sub"]
        return db.session.get(User, int(identity))

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return {"error": "invalid_token", "details": reason}, 401

    @jwt.expired_token_loader
    def _expired_token(_jwt_header, _jwt_payload):
        return {"error": "token_expired"}, 401

    @app.post("/api/auth/revoke")
    @jwt_required(verify_type=False)
    def revoke_current_token():
        claims = get_jwt()
        identity = get_jwt_identity()
        if identity is None:
            return {"error": "unauthorized"}, 401
        app.extensions["token_blocklist"].add(claims["jti"])
        return {"ok": True}

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.messages import messages_bp
    from .routes.moderation import moderation_bp
    from .sockets.chat import register_chat_namespace

    app.register_blueprint(auth_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(admin_bp)

    register_chat_namespace(socketio)

    with app.app_context():
        db.create_all()
        _seed_settings(app)
        _seed_default_users(app)

    return app
