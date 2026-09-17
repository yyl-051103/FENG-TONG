"""
Redis 连接工具，用于 JWT session 管理等场景
"""
import logging
import redis
from app.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger("uvicorn.error")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)


def add_active_session(jti: str) -> None:
    """添加活跃会话，TTL 固定 1 小时"""
    try:
        redis_client.setex(f"session:{jti}", 3600, "1")
    except Exception as e:
        logger.error(f"[Redis] add_active_session failed: {e}")


def is_session_active(jti: str) -> bool:
    """检查会话是否活跃"""
    try:
        return redis_client.exists(f"session:{jti}") > 0
    except Exception:
        return False


def remove_session(jti: str) -> None:
    """移除会话"""
    try:
        redis_client.delete(f"session:{jti}")
    except Exception as e:
        logger.error(f"[Redis] remove_session failed: {e}")
