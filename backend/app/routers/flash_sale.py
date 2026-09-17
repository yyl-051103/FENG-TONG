"""
抢购活动路由 - 用户端
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.gift import Gift
from app.models.flash_sale import FlashSale
from app.utils.redis_client import redis_client

router = APIRouter(prefix="/api/flash-sales", tags=["抢购"])


@router.get("")
def list_active_flash_sales(db: Session = Depends(get_db)):
    """返回进行中+即将开始的抢购列表，含倒计时服务端时间"""
    # 使用本地时间（与数据库存储的 naive datetime 对齐，避免 UTC 偏差）
    now = datetime.now()
    server_ts = now.timestamp()

    # 更新状态：全部活动（不过滤），保证已开始/已结束的都能被刷新
    all_sales = db.query(FlashSale).all()
    for fs in all_sales:
        if fs.status == "未开始" and now >= fs.start_time:
            fs.status = "进行中"
        elif fs.status == "进行中" and now >= fs.end_time:
            fs.status = "已结束"
    db.commit()

    # 查询未结束的活动（进行中 + 未开始）
    flash_sales = (
        db.query(FlashSale)
        .filter(FlashSale.end_time > now)
        .order_by(FlashSale.start_time.asc())
        .all()
    )

    items = []
    for fs in flash_sales:
        gift = db.query(Gift).filter(Gift.id == fs.gift_id).first()
        redis_stock = redis_client.get(f"flash:stock:{fs.id}")
        current_stock = int(redis_stock) if redis_stock else fs.flash_stock

        items.append({
            "id": fs.id,
            "gift_id": fs.gift_id,
            "gift_name": gift.name if gift else "",
            "gift_image": gift.image if gift else "",
            "gift_description": gift.description if gift else "",
            "flash_price_points": fs.flash_price_points,
            "flash_price_cash": float(fs.flash_price_cash) if fs.flash_price_cash else 0.00,
            "flash_stock": fs.flash_stock,
            "current_stock": current_stock,
            "start_time": fs.start_time.timestamp() if fs.start_time else None,
            "end_time": fs.end_time.timestamp() if fs.end_time else None,
            "start_time_str": fs.start_time.isoformat() if fs.start_time else None,
            "end_time_str": fs.end_time.isoformat() if fs.end_time else None,
            "status": fs.status,
        })

    return {
        "code": 200,
        "data": {
            "items": items,
            "server_time": server_ts,
        },
    }
