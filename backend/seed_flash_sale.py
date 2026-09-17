"""
种子数据：插入 1 条抢购测试数据
关联已有礼品，开放时间 = 当前 ~ 当前+3天
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.gift import Gift
from app.models.flash_sale import FlashSale

db = SessionLocal()

# 取第一个上架礼品
gift = db.query(Gift).filter(Gift.status == "上架").first()
if not gift:
    print("没有上架礼品，跳过种子数据")
    db.close()
    sys.exit(0)

# 检查是否已有抢购数据
existing = db.query(FlashSale).first()
if existing:
    print(f"已有抢购数据 (id={existing.id})，跳过")
    db.close()
    sys.exit(0)

now = datetime.now()
fs = FlashSale(
    gift_id=gift.id,
    flash_price_points=gift.points_required or 0,
    flash_price_cash=float(gift.price or 0) if gift.price else 0.0,
    flash_stock=10,
    start_time=now,
    end_time=now + timedelta(days=3),
    status="进行中",
    create_time=now,
)
db.add(fs)
db.commit()
db.refresh(fs)
print(f"种子数据已插入: flash_sale_id={fs.id}, gift_id={gift.id}, gift_name={gift.name}")

db.close()
