"""
订单模型 - Order + OrderItem
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Order(Base):
    __tablename__ = "`order`"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号 GIFT+时间戳+随机数")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    total_points = Column(Integer, default=0, comment="消耗积分")
    total_price = Column(DECIMAL(10, 2), default=0.00, comment="支付金额")
    status = Column(String(20), default="待支付", comment="订单状态")
    expire_time = Column(DateTime, nullable=True, comment="支付截止时间")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("`order`.id"), nullable=False, index=True)
    gift_id = Column(Integer, ForeignKey("gift.id"), nullable=False)
    quantity = Column(Integer, default=1, comment="数量")
    points_per_item = Column(Integer, default=0, comment="单品消耗积分")
    price_per_item = Column(DECIMAL(10, 2), default=0.00, comment="单品价格")

    order = relationship("Order", back_populates="items")
    gift = relationship("Gift")
