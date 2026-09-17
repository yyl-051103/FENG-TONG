"""
新闻相关模型 — 严格对齐原始 main_cs.py 中的 News / Comment / LikeRecord / FavoriteRecord 定义
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, func
from app.database import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    status = Column(String(20), default="待审核")
    risk_reason = Column(Text, nullable=True)
    risk_level = Column(String(10), nullable=True)
    create_time = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # 地图相关字段
    latitude = Column(Float, nullable=True, comment="纬度")
    longitude = Column(Float, nullable=True, comment="经度")
    location = Column(String(255), nullable=True, comment="地址描述")


class Comment(Base):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    nickname = Column(String(100), default="匿名用户")
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, default=func.now())


class LikeRecord(Base):
    __tablename__ = "like_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    liked = Column(Boolean, default=True)
    create_time = Column(DateTime, default=func.now())


class FavoriteRecord(Base):
    __tablename__ = "favorite_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    favorited = Column(Boolean, default=True)
    create_time = Column(DateTime, default=func.now())
