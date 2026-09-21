import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def normalize_database_url(value: str) -> str:
    """Normalize provider URLs accepted by common hosting platforms."""
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    return value


def _database_options(database_url: str) -> dict:
    if not database_url.startswith("postgresql+psycopg://"):
        return {}
    return {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }


DATABASE_URL = normalize_database_url(
    os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'ai_analis_rambutan.sqlite3'}",
    )
)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _database_options(DATABASE_URL)
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    UPLOAD_FOLDER = BASE_DIR / "instance" / "uploads"
    MODEL_FOLDER = BASE_DIR / "instance" / "models"
    ALLOWED_IMAGE_EXTENSIONS: ClassVar[set[str]] = {"jpg", "jpeg", "png", "webp"}
    # Never create production schemas implicitly; use Flask-Migrate explicitly.
    AUTO_CREATE_SCHEMA = os.getenv(
        "AUTO_CREATE_SCHEMA", "0" if DATABASE_URL.startswith("postgresql+") else "1"
    ) == "1"
