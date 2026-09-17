"""
积分服务 — 积分获取与消耗
"""
import json
import logging

import pika
from sqlalchemy import select, update
from app.config import RABBITMQ_URL
from app.database import SessionLocal
from app.models.score import ScoreRecord, ScoreType
from app.models.user import User
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

SCORE_QUEUE = "score.queue"
SCORE_EXCHANGE = "score.exchange"
SCORE_ROUTING_KEY = "score.earn"


def get_rabbitmq_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)


def publish_score_event(user_id: int, source: str, score: int, related_id: int, description: str):
    """发布积分事件到 RabbitMQ（HTTP 路由调用此函数，非阻塞）"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # 声明 exchange 和 queue
        channel.exchange_declare(exchange=SCORE_EXCHANGE, exchange_type="topic", durable=True)
        channel.queue_declare(queue=SCORE_QUEUE, durable=True)
        channel.queue_bind(exchange=SCORE_EXCHANGE, queue=SCORE_QUEUE, routing_key=SCORE_ROUTING_KEY)

        message = json.dumps({
            "user_id": user_id,
            "source": source,
            "score": score,
            "related_id": related_id,
            "description": description,
        })

        channel.basic_publish(
            exchange=SCORE_EXCHANGE,
            routing_key=SCORE_ROUTING_KEY,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),  # 消息持久化
        )
        channel.close()
        connection.close()
    except Exception as e:
        logger.error(f"发布积分事件失败: {e}")


async def earn_score(user_id: int, source: str, score: int, related_id: int, description: str = ""):
    """积分获取。使用防重锁避免重复计分"""
    lock_key = f"score:lock:{user_id}:{source}:{related_id}"

    # 检查防重锁
    if redis_client.exists(lock_key):
        logger.info(f"防重锁命中: {lock_key}")
        return

    # 设置防重锁 TTL 10s
    redis_client.setex(lock_key, 10, "1")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        new_balance = (user.score_balance or 0) + score

        record = ScoreRecord(
            user_id=user_id,
            type=ScoreType.earn,
            source=source,
            score=score,
            balance_after=new_balance,
            related_id=related_id,
            description=description,
        )
        db.add(record)

        # 更新用户积分余额
        db.execute(
            update(User).where(User.id == user_id).values(score_balance=new_balance)
        )

        db.commit()
        logger.info(f"积分获取: user={user_id}, source={source}, score=+{score}, balance={new_balance}")
    except Exception as e:
        db.rollback()
        logger.error(f"积分获取失败: {e}")
        # 失败时释放防重锁
        redis_client.delete(lock_key)
    finally:
        db.close()
