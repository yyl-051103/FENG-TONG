"""
JWT 认证工具 — access_token + refresh_token 生成和验证，密码哈希使用 passlib bcrypt，保留原始 SHA-256 兼容过渡
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__default_rounds=12, deprecated="auto")


def hash_password_sha256(password: str) -> str:
    """原始 SHA-256 哈希（过渡期保留）"""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    """bcrypt 哈希密码（对超长密码先 SHA-256 再 bcrypt）"""
    password_bytes = password.encode()
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode()
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码：先尝试 bcrypt，失败则回退到 SHA-256"""
    # bcrypt 哈希以 $2b$ 或 $2a$ 开头
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        plain_bytes = plain_password.encode()
        if len(plain_bytes) > 72:
            plain_bytes = hashlib.sha256(plain_bytes).hexdigest().encode()
        return pwd_context.verify(plain_bytes, hashed_password)
    # 回退到原始 SHA-256
    return hashed_password == hash_password_sha256(plain_password)


def generate_token_str() -> str:
    """生成随机 token 字符串（过渡期保留）"""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """生成 JWT access_token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """生成 JWT refresh_token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """验证 JWT token 并返回 payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
