"""
礼品模型 - Gift
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, func
from app.database import Base


class Gift(Base):
    __tablename__ = "gift"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="礼品名称")
    description = Column(String(500), nullable=True, comment="礼品描述")
    image = Column(String(500), nullable=True, comment="图片URL")
    points_required = Column(Integer, default=0, comment="所需积分")
    price = Column(DECIMAL(10, 2), default=0.00, comment="现金价格")
    stock = Column(Integer, default=0, comment="库存")
    category = Column(String(50), nullable=True, comment="类别：联名款/限定款/盲盒")
    status = Column(String(20), default="上架", comment="状态：上架/下架")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
