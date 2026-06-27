import os
from datetime import timedelta


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///chat.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = _as_bool(os.getenv("JWT_COOKIE_SECURE"), default=False)
    JWT_COOKIE_CSRF_PROTECT = _as_bool(os.getenv("JWT_COOKIE_CSRF_PROTECT"), default=False)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")

    LOW_THRESHOLD = float(os.getenv("LOW_THRESHOLD", "0.40"))
    HIGH_THRESHOLD = float(os.getenv("HIGH_THRESHOLD", "0.75"))
    FLOOD_COUNT = int(os.getenv("FLOOD_COUNT", "5"))
    FLOOD_WINDOW = int(os.getenv("FLOOD_WINDOW", "30"))
    DUPLICATE_WINDOW = int(os.getenv("DUPLICATE_WINDOW", "30"))
    TEMP_BLOCK_HOURS = int(os.getenv("TEMP_BLOCK_HOURS", "24"))
    MESSAGE_MAX_LENGTH = int(os.getenv("MESSAGE_MAX_LENGTH", "512"))
    ML_MODEL = os.getenv("ML_MODEL", "cointegrated/rubert-tiny-toxicity")
    STOPWORDS = os.getenv("STOPWORDS", "")
    SEED_DEFAULT_USERS = _as_bool(os.getenv("SEED_DEFAULT_USERS"), default=True)
    DEMO_USERS_PASSWORD = os.getenv("DEMO_USERS_PASSWORD", "demo12345")
    DEMO_USER_USERNAME = os.getenv("DEMO_USER_USERNAME", "demo_user")
    DEMO_MODERATOR_USERNAME = os.getenv("DEMO_MODERATOR_USERNAME", "demo_moderator")
    DEMO_ADMIN_USERNAME = os.getenv("DEMO_ADMIN_USERNAME", "demo_admin")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=10)
    ML_MODEL = "disabled"
    SEED_DEFAULT_USERS = False
