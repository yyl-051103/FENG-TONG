"""
积分路由 - 余额查询 / 积分明细 / 积分概览
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.score import ScoreRecord

router = APIRouter(prefix="/api/score", tags=["积分"])


@router.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前积分余额"""
    real_user = db.query(User).filter(User.id == current_user.id).first()
    balance = real_user.score_balance if real_user else 0
    return {"code": 200, "data": {"balance": balance}}


@router.get("/records")
def get_records(
    type: str = Query(None, description="筛选类型：earn/consume"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """积分明细列表，按时间倒序，支持类型筛选"""
    query = db.query(ScoreRecord).filter(ScoreRecord.user_id == current_user.id)
    if type:
        query = query.filter(ScoreRecord.type == type)

    total = query.count()
    records = (
        query.order_by(ScoreRecord.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "type": r.type.value if r.type else None,
            "source": r.source.value if r.source else None,
            "score": r.score,
            "balance_after": r.balance_after,
            "description": r.description,
            "create_time": r.create_time.isoformat() if r.create_time else None,
        })

    return {"code": 200, "data": {"total": total, "items": items}}


@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """积分统计概览"""
    earn_total = (
        db.query(func.sum(ScoreRecord.score))
        .filter(
            ScoreRecord.user_id == current_user.id,
            ScoreRecord.type == "earn",
        )
        .scalar()
    ) or 0

    consume_total = (
        db.query(func.sum(ScoreRecord.score))
        .filter(
            ScoreRecord.user_id == current_user.id,
            ScoreRecord.type == "consume",
        )
        .scalar()
    ) or 0

    real_user = db.query(User).filter(User.id == current_user.id).first()
    balance = real_user.score_balance if real_user else 0

    return {
        "code": 200,
        "data": {
            "balance": balance,
            "total_earn": earn_total,
            "total_consume": abs(consume_total),
        },
    }
