"""
抢购活动模型 - FlashSale
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, func
from app.database import Base


class FlashSale(Base):
    __tablename__ = "flash_sale"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gift_id = Column(Integer, ForeignKey("gift.id"), nullable=False, comment="关联礼品ID")
    flash_price_points = Column(Integer, default=0, comment="抢购积分价，0表示纯现金")
    flash_price_cash = Column(DECIMAL(10, 2), default=0.00, comment="抢购现金价")
    flash_stock = Column(Integer, default=0, comment="抢购库存量")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    status = Column(String(20), default="未开始", comment="状态：未开始/进行中/已结束")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
