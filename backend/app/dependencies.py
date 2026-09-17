"""
依赖注入 — get_db / get_current_user（JWT 认证）"""
from typing import Optional

from fastapi import Depends, HTTPException, Header

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import verify_token
from app.utils.redis_client import is_session_active


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> User:
    """从 Authorization Bearer Header 解析 JWT，返回当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")

    # 支持 "Bearer <token>" 和直接 token 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")

    # 检查 token 类型
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="无效的 token 类型")

    # 检查会话是否活跃
    jti = payload.get("jti", "")
    if jti and not is_session_active(jti):
        raise HTTPException(status_code=401, detail="会话已过期，请重新登录")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的 token")

    # 从 JWT payload 还原用户（不查库）
    user = User(
        id=int(user_id),
        username=payload.get("username", ""),
        nickname=payload.get("nickname", ""),
        role=payload.get("role", "user"),
    )

    return user


def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """可选认证：有 token 则解析，无则返回 None"""
    if not authorization:
        return None
    try:
        return get_current_user(authorization=authorization)
    except HTTPException:
        return None
