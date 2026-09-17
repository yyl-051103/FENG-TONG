"""
管理员礼品路由 - CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.gift import Gift

router = APIRouter(prefix="/api/admin/gifts", tags=["管理-礼品"])


class GiftCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    points_required: int = 0
    price: float = 0.00
    stock: int = 0
    category: Optional[str] = None
    status: str = "上架"


class GiftUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    points_required: Optional[int] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    status: Optional[str] = None


def _require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")


@router.post("")
def create_gift(
    body: GiftCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(user)
    gift = Gift(
        name=body.name,
        description=body.description,
        image=body.image,
        points_required=body.points_required,
        price=body.price,
        stock=body.stock,
        category=body.category,
        status=body.status,
    )
    db.add(gift)
    db.commit()
    db.refresh(gift)
    return {"code": 200, "data": {"id": gift.id}, "message": "创建成功"}


@router.put("/{gift_id}")
def update_gift(
    gift_id: int,
    body: GiftUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(user)
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="礼品不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(gift, key, value)

    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{gift_id}")
def delete_gift(
    gift_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(user)
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="礼品不存在")

    db.delete(gift)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.get("")
def admin_list_gifts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理端：全部礼品列表，含库存"""
    _require_admin(user)
    gifts = db.query(Gift).order_by(Gift.create_time.desc()).all()

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
