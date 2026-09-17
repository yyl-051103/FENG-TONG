"""
用户端礼品路由 - 礼品列表 / 礼品详情
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.gift import Gift

router = APIRouter(prefix="/api/gifts", tags=["礼品"])


@router.get("")
def list_gifts(
    category: str = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
):
    """用户端：只返回上架礼品，支持分类筛选"""
    query = db.query(Gift).filter(Gift.status == "上架")
    if category:
        query = query.filter(Gift.category == category)

    gifts = query.order_by(Gift.create_time.desc()).all()

    items = []
    for g in gifts:
        items.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "image": g.image,
            "points_required": g.points_required,
            "price": float(g.price) if g.price else 0.00,
            "stock": g.stock,
            "category": g.category,
            "status": g.status,
            "create_time": g.create_time.isoformat() if g.create_time else None,
        })

    return {"code": 200, "data": {"items": items}}


@router.get("/{gift_id}")
def get_gift_detail(
    gift_id: int,
    db: Session = Depends(get_db),
):
    """用户端：礼品详情"""
    g = db.query(Gift).filter(Gift.id == gift_id, Gift.status == "上架").first()
    if not g:
        raise HTTPException(status_code=404, detail="礼品不存在或已下架")

    return {
        "code": 200,
        "data": {
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "image": g.image,
            "points_required": g.points_required,
            "price": float(g.price) if g.price else 0.00,
            "stock": g.stock,
            "category": g.category,
            "status": g.status,
            "create_time": g.create_time.isoformat() if g.create_time else None,
        },
    }
