import os
from pathlib import Path

from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)


class BaseConfig:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    API_KEYS = [item.strip() for item in os.getenv("API_KEYS", "local-api-key").split(",") if item.strip()]
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    FLASK_ENV = "production"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    JWT_SECRET_KEY = "test-secret"
    API_KEYS = ["test-api-key"]


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
