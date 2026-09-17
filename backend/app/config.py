"""Application configuration loaded from the environment or a local .env file."""

import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    """Return a non-placeholder setting or fail with an actionable startup error."""
    value = os.getenv(name, "").strip()
    if not value or value.startswith("CHANGE_ME_"):
        raise RuntimeError(f"{name} must be set in .env or the environment")
    return value


# MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = require_env("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "news_platform")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_URL = os.getenv("ES_URL", "http://localhost:9200")

# RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = require_env("RABBITMQ_USER")
RABBITMQ_PASSWORD = require_env("RABBITMQ_PASSWORD")
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/",
)

# Authentication
JWT_SECRET_KEY = require_env("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
ADMIN_INVITE_CODE = os.getenv("ADMIN_INVITE_CODE", "").strip()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

# Optional integrations. Their respective feature validates credentials at use time.
DIFY_CREATIVE_API_KEY = os.getenv("DIFY_CREATIVE_API_KEY", "")
DIFY_RISK_API_KEY = os.getenv("DIFY_RISK_API_KEY", "")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/workflows/run")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Alipay
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_GATEWAY = os.getenv("ALIPAY_GATEWAY", "https://openapi-sandbox.dl.alipaydev.com/gateway.do")
ALIPAY_REDIRECT_URI = os.getenv("ALIPAY_REDIRECT_URI", "http://localhost:3000/checkout/callback")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL", "http://localhost:8000/api/alipay/notify")
