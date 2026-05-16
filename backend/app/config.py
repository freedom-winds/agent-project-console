"""Application configuration."""
import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class Config:
    SECRET_KEY = os.environ.get("APC_SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "APC_DATABASE_URI",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "apc.sqlite3"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    HOST = os.environ.get("APC_HOST", "127.0.0.1")
    PORT = int(os.environ.get("APC_PORT", "8765"))
    CORS_ORIGINS = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
