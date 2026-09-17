"""
用户路由 — 收藏列表
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.news import News, FavoriteRecord

router = APIRouter()


@router.get("/favorites")
def get_my_favorites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的收藏列表"""
    fav_records = (
        db.query(FavoriteRecord)
        .filter(
            FavoriteRecord.user_id == user.id,
            FavoriteRecord.favorited == True,
        )
        .all()
    )

    result = []
    for record in fav_records:
        news = db.query(News).filter(News.id == record.news_id).first()
        if news:
            result.append(
                {
                    "id": news.id,
                    "title": news.title,
                    "create_time": news.create_time,
                    "source": news.source,
                }
            )
    return result
