"""
积分记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from datetime import datetime
from app.database import Base
import enum


class ScoreType(str, enum.Enum):
    earn = "earn"
    consume = "consume"


class ScoreSource(str, enum.Enum):
    comment = "comment"
    like = "like"
    favorite = "favorite"
    publish_news = "publish_news"
    gift_exchange = "gift_exchange"
    refund = "refund"
    admin_adjust = "admin_adjust"


class ScoreRecord(Base):
    __tablename__ = "score_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    type = Column(SQLEnum(ScoreType), nullable=False, comment="积分类型：earn获取/consume消耗")
    source = Column(SQLEnum(ScoreSource), nullable=False, comment="来源")
    score = Column(Integer, nullable=False, comment="积分变动数量，正数为获取负数为消耗")
    balance_after = Column(Integer, nullable=False, comment="变动后积分余额")
    related_id = Column(Integer, comment="关联业务ID")
    description = Column(String(255), comment="变动描述")
    create_time = Column(DateTime, default=datetime.now, index=True)
