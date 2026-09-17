"""
新闻路由 — 发布 / 列表 / 详情 / 删除 / 点赞 / 收藏 / 评论
"""
import traceback
import sys
import requests
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, get_optional_user
from app.models.user import User
from app.models.news import News, Comment, LikeRecord, FavoriteRecord
from app.schemas.news import NewsPublishRequest, CommentRequest
from app.config import DIFY_RISK_API_KEY, DIFY_API_URL
from app.services.search_service import sync_news, delete_news, tokenize_text
from app.services.score_service import publish_score_event

router = APIRouter()


def _log(msg: str):
    print(f"[Dify-风控] {msg}", file=sys.stderr, flush=True)


def call_risk_dify(title: str, content: str) -> dict:
    headers = {
        "Authorization": f"Bearer {DIFY_RISK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "inputs": {"biao_ti": title, "nei_rong": content},
        "response_mode": "blocking",
        "user": "user",
    }
    try:
        _log(f"调用中: title={title[:30]}")
        res = requests.post(DIFY_API_URL, json=data, headers=headers, timeout=60)
        _log(f"响应: status={res.status_code}, body前200={res.text[:200]}")
        text = res.json()["data"]["outputs"]["text"]
        _log(f"成功: text前100={text[:100]}")
    except KeyError:
        _log("outputs 无 text 字段(内容合规)")
        text = "正常"
    except requests.Timeout:
        _log("超时: 风控工作流超时，转管理员审核")
        return {"is_violate": False, "reason": "审核超时，待管理员处理", "risk_level": "审核中"}
    except Exception as e:
        _log(f"失败: {type(e).__name__}: {e}")
        _log(f"Traceback: {traceback.format_exc()}")
        text = "正常"

    if "高" in text:
        return {"is_violate": True, "reason": text, "risk_level": "高"}
    elif "中" in text:
        return {"is_violate": True, "reason": text, "risk_level": "中"}
    elif "低" in text:
        return {"is_violate": True, "reason": text, "risk_level": "低"}
    else:
        return {"is_violate": False, "reason": "内容合规", "risk_level": "正常"}

@router.post("/publish")
async def publish_news(
    req: NewsPublishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布新闻 — Dify 风控审核"""
    risk = call_risk_dify(req.title, req.content)
    level = risk["risk_level"]

    if level == "审核中":
        status = "待审核"
        msg = "审核超时，转管理员审核"
    elif level == "高":
        status = "已拒绝"
        msg = "内容高风险，拒绝发布"
    elif level in ["中", "低"]:
        status = "待审核"
        msg = "提交成功，等待管理员审核"
    else:
        status = "已通过"
        msg = "发布成功，内容合规"

    # 自动解析地址经纬度
    latitude = req.latitude
    longitude = req.longitude
    if req.location and (latitude is None or longitude is None):
        from app.services.map_service import geocode
        geo = await geocode(req.location)
        if geo:
            latitude = geo["lat"]
            longitude = geo["lng"]

    news = News(
        title=req.title,
        content=req.content,
        source=req.source,
        status=status,
        risk_reason=risk["reason"],
        risk_level=risk["risk_level"],
        user_id=user.id,
        latitude=latitude,
        longitude=longitude,
        location=req.location,
    )
    db.add(news)
    db.commit()

    # 审核通过后同步到ES
    if status == "已通过":
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
            "nickname": user.nickname or "匿名",
            "create_time": news.create_time.isoformat() if news.create_time else None,
        }
        await sync_news(news_dict)
        publish_score_event(
            user_id=user.id,
            source="publish_news",
            score=3,
            related_id=news.id,
            description=f"发布新闻#{news.id}",
        )

    return {
        "code": 200,
        "status": status,
        "msg": msg,
        "risk_level": risk["risk_level"],
        "news_id": news.id,
    }


@router.get("/list")
def news_list(db: Session = Depends(get_db)):
    """首页新闻列表 — 仅已通过"""
    return (
        db.query(News)
        .filter(News.status == "已通过")
        .order_by(News.create_time.desc())
        .all()
    )


@router.get("/detail/{news_id}")
def news_detail(news_id: int, db: Session = Depends(get_db)):
    """新闻详情"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 返回与原始代码一致的字段（包括 nickname）
    user = db.query(User).filter(User.id == news.user_id).first()
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "source": news.source,
        "status": news.status,
        "risk_reason": news.risk_reason,
        "risk_level": news.risk_level,
        "create_time": news.create_time,
        "user_id": news.user_id,
        "nickname": user.nickname if user else "匿名",
    }


@router.delete("/{news_id}")
async def del_news(
    news_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除新闻 — 先删关联数据再删新闻"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404)

    if user.role != "admin" and news.user_id != user.id:
        raise HTTPException(status_code=403)

    # 先删关联数据
    db.query(LikeRecord).filter(LikeRecord.news_id == news_id).delete()
    db.query(FavoriteRecord).filter(FavoriteRecord.news_id == news_id).delete()
    db.query(Comment).filter(Comment.news_id == news_id).delete()
    db.delete(news)
    db.commit()

    # 从ES删除
    await delete_news(news_id)

    return {"code": 200, "msg": "删除成功"}


@router.get("/my")
def my_news(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的发布"""
    return (
        db.query(News)
        .filter(News.user_id == user.id)
        .order_by(News.create_time.desc())
        .all()
    )


# ── 点赞 ──
@router.post("/{news_id}/like")
async def toggle_like(
    news_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = (
        db.query(LikeRecord)
        .filter(LikeRecord.news_id == news_id, LikeRecord.user_id == user.id)
        .first()
    )
    is_new = rec is None
    if rec:
        rec.liked = not rec.liked
    else:
        rec = LikeRecord(news_id=news_id, user_id=user.id, liked=True)
        db.add(rec)
    db.commit()

    # 首次点赞触发积分
    if is_new:
        publish_score_event(
            user_id=user.id,
            source="like",
            score=1,
            related_id=rec.id,
            description=f"点赞新闻#{news_id}",
        )

    return {"liked": rec.liked}


# ── 收藏 ──
@router.post("/{news_id}/favorite")
async def toggle_favorite(
    news_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = (
        db.query(FavoriteRecord)
        .filter(FavoriteRecord.news_id == news_id, FavoriteRecord.user_id == user.id)
        .first()
    )
    is_new = rec is None
    if rec:
        rec.favorited = not rec.favorited
    else:
        rec = FavoriteRecord(news_id=news_id, user_id=user.id, favorited=True)
        db.add(rec)
    db.commit()

    # 首次收藏触发积分
    if is_new:
        publish_score_event(
            user_id=user.id,
            source="favorite",
            score=1,
            related_id=rec.id,
            description=f"收藏新闻#{news_id}",
        )

    return {"favorited": rec.favorited}


# ── 统计 ──
@router.get("/{news_id}/stats")
def news_stats(
    news_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    like_count = (
        db.query(LikeRecord)
        .filter(LikeRecord.news_id == news_id, LikeRecord.liked == True)
        .count()
    )
    fav_count = (
        db.query(FavoriteRecord)
        .filter(FavoriteRecord.news_id == news_id, FavoriteRecord.favorited == True)
        .count()
    )
    comment_count = (
        db.query(Comment).filter(Comment.news_id == news_id).count()
    )

    is_liked = False
    is_favorited = False
    if user:
        is_liked = (
            db.query(LikeRecord)
            .filter(
                LikeRecord.news_id == news_id,
                LikeRecord.user_id == user.id,
                LikeRecord.liked == True,
            )
            .first()
            is not None
        )
        is_favorited = (
            db.query(FavoriteRecord)
            .filter(
                FavoriteRecord.news_id == news_id,
                FavoriteRecord.user_id == user.id,
                FavoriteRecord.favorited == True,
            )
            .first()
            is not None
        )

    return {
        "like_count": like_count,
        "favorite_count": fav_count,
        "comment_count": comment_count,
        "is_liked": is_liked,
        "is_favorited": is_favorited,
    }


# ── 评论 ──
@router.get("/{news_id}/comments")
def get_comments(news_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(Comment)
        .filter(Comment.news_id == news_id)
        .order_by(Comment.create_time.desc())
        .all()
    )
    return comments


@router.post("/{news_id}/comment")
async def post_comment(
    news_id: int,
    content: str = Query(..., description="评论内容"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发表评论 — 使用 Query 参数（与原始代码一致）"""
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    comment = Comment(
        news_id=news_id,
        user_id=user.id,
        nickname=user.nickname or "匿名用户",
        content=content,
    )
    db.add(comment)
    db.commit()

    # 评论成功触发积分
    publish_score_event(
        user_id=user.id,
        source="comment",
        score=1,
        related_id=comment.id,
        description=f"评论新闻#{news_id}",
    )

    return {"code": 200, "msg": "评论成功"}
