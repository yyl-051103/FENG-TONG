"""
订单超时扫描器 — 每 10 秒扫描 Redis Sorted Set，自动取消超时未支付订单
"""
import os
import json
import time
import threading
import logging
from datetime import datetime

from app.utils.redis_client import redis_client
from app.database import SessionLocal
from app.models.user import User
from app.models.gift import Gift
from app.models.order import Order, OrderItem
from app.models.flash_sale import FlashSale
from app.models.score import ScoreRecord, ScoreType, ScoreSource
from app.services import alipay_service

logger = logging.getLogger(__name__)

TIMEOUT_KEY = "order:timeout"
SCAN_INTERVAL = 10  # 秒


def start_timeout_scanner():
    """启动订单超时扫描线程"""

    def scan():
        while True:
            try:
                now = int(time.time())
                # Lua 原子：取回过期的 order_no 并移除
                lua = """
                local key = KEYS[1]
                local limit = tonumber(ARGV[1])
                local expired = redis.call('ZRANGEBYSCORE', key, 0, limit)
                if #expired > 0 then
                    redis.call('ZREM', key, unpack(expired))
                end
                return expired
                """
                expired_orders = redis_client.eval(lua, 1, TIMEOUT_KEY, now)

                if not expired_orders:
                    time.sleep(SCAN_INTERVAL)
                    continue

                logger.info(f"[TimeoutScanner] 发现 {len(expired_orders)} 个过期订单")

                db = SessionLocal()
                for raw in expired_orders:
                    order_no = raw.decode() if isinstance(raw, bytes) else raw
                    try:
                        _cancel_expired_order(db, order_no)
                    except Exception:
                        logger.exception(f"[TimeoutScanner] 超时取消订单失败: {order_no}")
                db.close()
                time.sleep(SCAN_INTERVAL)

            except Exception:
                logger.exception("[TimeoutScanner] 扫描异常")
                time.sleep(SCAN_INTERVAL)

    thread = threading.Thread(target=scan, daemon=True)
    thread.start()
    logger.info("[TimeoutScanner] 订单超时扫描器已启动")


def _cancel_expired_order(db, order_no: str):
    """取消一个已过期的待支付订单"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order or order.status != "待支付":
        return

    # 查询支付宝确认是否实际上已支付（防止竞态）
    try:
        if float(order.total_price or 0) > 0:
            paid = alipay_service.query_order(order_no)
            if paid:
                order.status = "已支付"
                db.commit()
                logger.info(f"[TimeoutScanner] 订单 {order_no} 超时扫描发现已支付，补同步")
                return
    except Exception:
        pass

    # 确认未支付 → 取消订单
    order.status = "已取消"

    # 恢复库存
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for oi in order_items:
        gift = db.query(Gift).filter(Gift.id == oi.gift_id).first()
        if gift:
            gift.stock += oi.quantity
            # 恢复 Redis 礼品库存
            redis_client.incrby(f"gift:stock:{gift.id}", oi.quantity)
            # 恢复关联的抢购 Redis 库存
            flash_sales = db.query(FlashSale).filter(
                FlashSale.gift_id == gift.id,
                FlashSale.status != "已结束"
            ).all()
            for fs in flash_sales:
                redis_client.incrby(f"flash:stock:{fs.id}", oi.quantity)

    # 退还积分
    if order.total_points and order.total_points > 0:
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            user.score_balance = (user.score_balance or 0) + order.total_points
            db.add(ScoreRecord(
                user_id=user.id,
                type=ScoreType.earn,
                source=ScoreSource.refund,
                score=order.total_points,
                balance_after=user.score_balance,
                description=f"支付超时自动取消，退还积分，订单号 {order_no}",
                create_time=datetime.now(),
            ))

    db.commit()
    logger.info(f"[TimeoutScanner] 订单 {order_no} 支付超时，已自动取消")
