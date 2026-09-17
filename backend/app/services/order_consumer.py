"""
RabbitMQ 抢兑消费者 — 串行消费 order.queue，原子扣库存后创建订单
"""
import json
import os
import threading
import logging
import random
import time
from datetime import datetime, timedelta

import pika

from app.config import RABBITMQ_URL
from app.utils.redis_client import redis_client
from app.database import SessionLocal
from app.models.user import User
from app.models.gift import Gift
from app.models.order import Order, OrderItem
from app.models.flash_sale import FlashSale
from app.services.stock import deduct_flash_stock, deduct_stock

logger = logging.getLogger(__name__)

ORDER_QUEUE = "order.queue"
RESULT_PREFIX = "order:result:"
RESULT_TTL = 60  # 秒


def start_order_consumer():
    """启动订单消费者线程"""

    def callback(ch, method, properties, body):
        db = SessionLocal()
        try:
            data = json.loads(body)
            user_id = data["user_id"]
            gift_id = data["gift_id"]
            flash_sale_id = data.get("flash_sale_id")
            quantity = data.get("quantity", 1)
            use_points_input = data.get("use_points", True)  # 用户支付方式选择

            # 1. 根据是否抢购选择库存扣减策略
            order = None  # 初始化为 None，防止库存不足时未赋值
            if flash_sale_id:
                # 抢购模式：扣 Redis 抢购库存
                ok, remaining = deduct_flash_stock(flash_sale_id, quantity)
                if not ok:
                    result = {"success": False, "reason": "抢购库存不足"}
                else:
                    # 同步扣礼品库存
                    deduct_stock(gift_id, quantity)

                    # 获取抢购价格
                    fs = db.query(FlashSale).filter(FlashSale.id == flash_sale_id).first()
                    flash_points = fs.flash_price_points if fs else 0
                    flash_cash = float(fs.flash_price_cash) if fs and fs.flash_price_cash else 0.00

                    order, is_points_only = _create_order_in_db(
                        db, user_id, gift_id, quantity,
                        flash_points, flash_cash,
                        flash_sale_id, use_points_input
                    )
                    db.commit()
                    result = {
                        "success": True,
                        "order_no": order.order_no,
                        "order_id": order.id,
                        "total_points": order.total_points,
                        "total_price": float(order.total_price) if order.total_price else 0.00,
                        "status": order.status,
                    }
            else:
                # 普通下单模式：扣 Redis 礼品库存
                ok, remaining = deduct_stock(gift_id, quantity)
                if not ok:
                    result = {"success": False, "reason": "库存不足"}
                else:
                    gift = db.query(Gift).filter(Gift.id == gift_id).first()
                    points_needed = (gift.points_required or 0) * quantity
                    price = float(gift.price or 0) * quantity

                    order, is_points_only = _create_order_in_db(
                        db, user_id, gift_id, quantity,
                        points_needed, price,
                        use_points_input=use_points_input
                    )
                    db.commit()
                    result = {
                        "success": True,
                        "order_no": order.order_no,
                        "order_id": order.id,
                        "total_points": order.total_points,
                        "total_price": float(order.total_price) if order.total_price else 0.00,
                        "status": order.status,
                    }

            # 2. 仅非纯积分订单需要支付超时定时器（纯积分直接完成，无需延迟）
            if order is not None and not is_points_only:
                payment_window = int(os.getenv("PAYMENT_WINDOW_MINUTES", "15"))
                expire_ts = int(time.time()) + payment_window * 60
                redis_client.zadd("order:timeout", {order.order_no: expire_ts})

            # 3. 结果写入 Redis，60s TTL
            redis_client.setex(
                f"{RESULT_PREFIX}{user_id}",
                RESULT_TTL,
                json.dumps(result)
            )
            logger.info(f"[OrderConsumer] user={user_id} result={result['success']}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"[OrderConsumer] 处理失败: {e}")
            try:
                redis_client.setex(
                    f"{RESULT_PREFIX}{data.get('user_id', 'unknown')}",
                    RESULT_TTL,
                    json.dumps({"success": False, "reason": f"系统错误: {str(e)}"})
                )
            except Exception:
                pass
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            db.close()

    def run():
        while True:
            try:
                params = pika.URLParameters(RABBITMQ_URL)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.queue_declare(queue=ORDER_QUEUE, durable=True, exclusive=False)
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=ORDER_QUEUE, on_message_callback=callback)
                logger.info("[OrderConsumer] 订单消费者已启动，等待消息...")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"[OrderConsumer] 连接断开，5秒后重连: {e}")
                time.sleep(5)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.info("[OrderConsumer] 订单消费者线程已启动")


def _create_order_in_db(db, user_id, gift_id, quantity, points_needed, price, flash_sale_id=None, use_points_input=True):
    """在 DB 中创建订单，处理积分扣减。返回 (order, is_points_only)"""
    user = db.query(User).filter(User.id == user_id).first()
    gift = db.query(Gift).filter(Gift.id == gift_id).first()

    # 判断积分是否足够 & 用户是否选择使用积分
    user_balance = user.score_balance or 0
    use_points = use_points_input and points_needed > 0 and user_balance >= points_needed

    ts = str(int(time.time() * 1000))
    rand_suffix = str(random.randint(1000, 9999))
    prefix = "FLASH" if flash_sale_id else "GIFT"
    order_no = f"{prefix}{ts}{rand_suffix}"

    if use_points:
        user.score_balance = user_balance - points_needed
        total_points = points_needed
        total_price = 0.00
    else:
        total_points = 0
        total_price = price

    # 纯积分兑换：订单直接完成，无需支付超时
    is_points_only = use_points and total_price == 0.00
    status = "已支付" if is_points_only else "待支付"
    expire_time = None if is_points_only else datetime.now() + timedelta(minutes=int(os.getenv("PAYMENT_WINDOW_MINUTES", "15")))

    order = Order(
        order_no=order_no,
        user_id=user_id,
        total_points=total_points,
        total_price=total_price,
        status=status,
        expire_time=expire_time,
    )
    db.add(order)
    db.flush()

    # 扣 DB 库存
    if gift and gift.stock >= quantity:
        gift.stock -= quantity

    order_item = OrderItem(
        order_id=order.id,
        gift_id=gift_id,
        quantity=quantity,
        points_per_item=points_needed // quantity if quantity > 0 else 0,
        price_per_item=price / quantity if quantity > 0 else 0.00,
    )
    db.add(order_item)

    # 积分记录
    if use_points:
        from app.models.score import ScoreRecord, ScoreType, ScoreSource
        score_record = ScoreRecord(
            user_id=user_id,
            type=ScoreType.consume,
            source=ScoreSource.gift_exchange,
            score=-total_points,
            balance_after=user.score_balance,
            description=f"{'抢购' if flash_sale_id else '兑换'}礼品，订单号 {order_no}",
            create_time=datetime.now(),
        )
        db.add(score_record)

    return order, is_points_only


# 独立入口：python -m app.services.order_consumer
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_order_consumer()
    import signal
    signal.pause()
