"""
抢购活动路由 - 管理端 CRUD
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.gift import Gift
from app.models.flash_sale import FlashSale
from app.utils.redis_client import redis_client

router = APIRouter(prefix="/api/admin/flash-sales", tags=["抢购管理"])


class FlashSaleCreate(BaseModel):
    gift_id: int
    flash_price_points: int = 0
    flash_price_cash: float = 0.00
    flash_stock: int
    start_time: str  # ISO 格式
    end_time: str


class FlashSaleUpdate(BaseModel):
    gift_id: Optional[int] = None
    flash_price_points: Optional[int] = None
    flash_price_cash: Optional[float] = None
    flash_stock: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None


def _admin_only(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")


@router.post("")
def create_flash_sale(
    body: FlashSaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _admin_only(current_user)

    gift = db.query(Gift).filter(Gift.id == body.gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="礼品不存在")

    start_time = datetime.fromisoformat(body.start_time)
    end_time = datetime.fromisoformat(body.end_time)

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

    now = datetime.now()
    if end_time <= now:
        initial_status = "已结束"
    elif start_time <= now:
        initial_status = "进行中"
    else:
        initial_status = "未开始"

    fs = FlashSale(
        gift_id=body.gift_id,
        flash_price_points=body.flash_price_points,
        flash_price_cash=body.flash_price_cash,
        flash_stock=body.flash_stock,
        start_time=start_time,
        end_time=end_time,
        status=initial_status,
    )
    db.add(fs)
    db.commit()
    db.refresh(fs)

    # 预热 Redis 抢购库存
    redis_client.set(f"flash:stock:{fs.id}", body.flash_stock)

    return {"code": 200, "data": _to_dict(fs), "message": "创建成功"}


@router.put("/{flash_sale_id}")
def update_flash_sale(
    flash_sale_id: int,
    body: FlashSaleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _admin_only(current_user)

    fs = db.query(FlashSale).filter(FlashSale.id == flash_sale_id).first()
    if not fs:
        raise HTTPException(status_code=404, detail="抢购活动不存在")

    if body.gift_id is not None:
        fs.gift_id = body.gift_id
    if body.flash_price_points is not None:
        fs.flash_price_points = body.flash_price_points
    if body.flash_price_cash is not None:
        fs.flash_price_cash = body.flash_price_cash
    if body.flash_stock is not None:
        fs.flash_stock = body.flash_stock
        redis_client.set(f"flash:stock:{fs.id}", body.flash_stock)
    if body.start_time is not None:
        fs.start_time = datetime.fromisoformat(body.start_time)
    if body.end_time is not None:
        fs.end_time = datetime.fromisoformat(body.end_time)
    if body.status is not None:
        fs.status = body.status

    db.commit()
    db.refresh(fs)
    return {"code": 200, "data": _to_dict(fs), "message": "更新成功"}


@router.delete("/{flash_sale_id}")
def delete_flash_sale(
    flash_sale_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _admin_only(current_user)

    fs = db.query(FlashSale).filter(FlashSale.id == flash_sale_id).first()
    if not fs:
        raise HTTPException(status_code=404, detail="抢购活动不存在")

    db.delete(fs)
    db.commit()
    redis_client.delete(f"flash:stock:{flash_sale_id}")
    return {"code": 200, "message": "删除成功"}


@router.get("")
def list_flash_sales(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _admin_only(current_user)

    flash_sales = db.query(FlashSale).order_by(FlashSale.create_time.desc()).all()
    items = []
    for fs in flash_sales:
        d = _to_dict(fs)
        gift = db.query(Gift).filter(Gift.id == fs.gift_id).first()
        d["gift_name"] = gift.name if gift else "已删除礼品"
        # 更新状态
        now = datetime.now()
        if fs.status != "已结束" and now >= fs.end_time:
            fs.status = "已结束"
            db.commit()
            d["status"] = "已结束"
        elif fs.status == "未开始" and now >= fs.start_time:
            fs.status = "进行中"
            db.commit()
            d["status"] = "进行中"
        items.append(d)

    return {"code": 200, "data": {"items": items}}


def _to_dict(fs: FlashSale) -> dict:
    return {
        "id": fs.id,
        "gift_id": fs.gift_id,
        "flash_price_points": fs.flash_price_points,
        "flash_price_cash": float(fs.flash_price_cash) if fs.flash_price_cash else 0.00,
        "flash_stock": fs.flash_stock,
        "start_time": fs.start_time.isoformat() if fs.start_time else None,
        "end_time": fs.end_time.isoformat() if fs.end_time else None,
        "status": fs.status,
        "create_time": fs.create_time.isoformat() if fs.create_time else None,
    }
