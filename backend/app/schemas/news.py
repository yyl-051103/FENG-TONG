"""
新闻相关的 Pydantic 请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel


class NewsPublishRequest(BaseModel):
    title: str
    content: str
    source: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


class AIAssistRequest(BaseModel):
    original_content: str
    assist_type: str
    title: Optional[str] = "未设置标题"


class CommentRequest(BaseModel):
    content: str
