"""
AI创作记录模型 ?严格对齐原始 main_cs.py 中的 AICreationRecord 定义
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class AICreationRecord(Base):
    __tablename__ = "ai_creation_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_content = Column(Text, nullable=False)
    optimized_content = Column(Text, nullable=False)
    assist_type = Column(String(50), nullable=False)
    create_time = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
