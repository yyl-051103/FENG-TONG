"""
管理员路由 — 新闻管理 / 审核 / 用户统计 / 全部 AI 记录
忠实还原原始 main_cs.py 逻辑
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.news import News
from app.models.ai_record import AICreationRecord
from app.services.search_service import sync_news, delete_news, tokenize_text

router = APIRouter()


@router.get("/news")
def admin_news(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全部新闻（管理员）"""
    if user.role != "admin":
        raise HTTPException(status_code=403)

    news_list = db.query(News).order_by(News.create_time.desc()).all()
    result = []
    for news in news_list:
        news_user = db.query(User).filter(User.id == news.user_id).first()
        result.append({
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "source": news.source,
            "status": news.status,
            "risk_reason": news.risk_reason,
            "risk_level": news.risk_level,
            "create_time": news.create_time,
            "user_id": news.user_id,
            "nickname": news_user.nickname if news_user else "匿名",
        })
    return result


@router.put("/news/{news_id}/review")
async def review_news(
    news_id: int,
    status: str = Query(..., description="审核状态：已通过 / 已拒绝 / 待审核"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """审核新闻"""
    if user.role != "admin":
        raise HTTPException(status_code=403)

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404)

    news.status = status
    db.commit()

    # 审核通过后同步到ES，非通过则从ES删除
    if status == "已通过":
        news_user = db.query(User).filter(User.id == news.user_id).first()
        news_dict = {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "title_tokens": tokenize_text(news.title or ""),
            "content_tokens": tokenize_text(news.content or ""),
            "source": news.source,
            "status": news.status,
            "risk_level": news.risk_level,
            "province": None,
            "city": None,
            "user_id": news.user_id,
            "nickname": news_user.nickname if news_user else "匿名",
            "create_time": news.create_time.isoformat() if news.create_time else None,
        }
        await sync_news(news_dict)
    else:
        await delete_news(news_id)

    return {"code": 200}


@router.get("/user/stats")
def admin_user_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户统计"""
    if user.role != "admin":
        raise HTTPException(status_code=403)

    total_users = db.query(User).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    normal_count = db.query(User).filter(User.role == "user").count()

    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "normal_count": normal_count,
    }


@router.get("/ai/records")
def admin_get_all_ai_records(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员查看所有 AI 创作记录"""
    if user.role != "admin":
        raise HTTPException(status_code=403)

    records = (
        db.query(AICreationRecord, User.username, User.nickname)
        .join(User, AICreationRecord.user_id == User.id)
        .order_by(AICreationRecord.create_time.desc())
        .all()
    )

    result = []
    for rec, username, nickname in records:
        result.append(
            {
                "id": rec.id,
                "username": username,
                "nickname": nickname or "匿名用户",
                "original_content": rec.original_content,
                "optimized_content": rec.optimized_content,
                "assist_type": rec.assist_type,
                "create_time": rec.create_time,
            }
        )

    return result
