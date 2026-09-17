"""
用户模型 ?严格对齐原始 main_cs.py 中的 User 定义
原始字段: id, username, password_hash, role, nickname, create_time, token
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(64), nullable=False)
    role = Column(String(20), default="user")
    nickname = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=func.now())
    score_balance = Column(Integer, default=0, comment="积分余额")
    phone = Column(String(11), unique=True, nullable=True, comment="手机号")
    # 过渡期内保留 token 字段
    token = Column(String(64), nullable=True)
