"""
积分消费者 — 从 RabbitMQ score.queue 消费积分事件，异步写入数据库
"""
import json
import threading
import logging
import pika
from app.config import RABBITMQ_URL

logger = logging.getLogger(__name__)

SCORE_QUEUE = "score.queue"


def start_score_consumer():
    """启动积分消费者线程，集成在 FastAPI 进程中运行"""

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            # 延迟导入避免循环依赖
            from app.services.score_service import earn_score
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(earn_score(
                user_id=data["user_id"],
                source=data["source"],
                score=data["score"],
                related_id=data["related_id"],
                description=data.get("description", ""),
            ))
            loop.close()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"积分消费成功: user={data['user_id']}, source={data['source']}")
        except Exception as e:
            logger.error(f"积分消费失败: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def run():
        while True:
            try:
                params = pika.URLParameters(RABBITMQ_URL)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.queue_declare(queue=SCORE_QUEUE, durable=True)
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=SCORE_QUEUE, on_message_callback=callback)
                logger.info("积分消费者已启动，等待消息...")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"积分消费者连接断开，5秒后重连: {e}")
                import time
                time.sleep(5)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.info("积分消费者线程已启动")
