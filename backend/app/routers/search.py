"""
搜索路由 — 新闻全文搜索
"""
from fastapi import APIRouter, Query
from app.services.search_service import search_news

router = APIRouter(prefix="/api/search", tags=["搜索"])


@router.get("/news")
async def search_news_api(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码")
):
    result = await search_news(q, page)
    return {"code": 200, "data": result}
