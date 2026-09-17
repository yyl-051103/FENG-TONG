"""
Redis 库存服务 — 礼品库存 + 抢购库存的 Redis 原子操作
"""
import logging
from app.utils.redis_client import redis_client
from app.database import SessionLocal
from app.models.gift import Gift

logger = logging.getLogger("uvicorn.error")

GIFT_STOCK_PREFIX = "gift:stock:"
FLASH_STOCK_PREFIX = "flash:stock:"


def init_stock():
    """启动时将所有上架礼品库存加载到 Redis，同时清理旧的抢购库存 key"""
    db = SessionLocal()
    try:
        gifts = db.query(Gift).filter(Gift.status == "上架").all()
        for gift in gifts:
            key = f"{GIFT_STOCK_PREFIX}{gift.id}"
            redis_client.set(key, gift.stock)
        logger.info(f"[Stock] 已初始化 {len(gifts)} 个礼品库存到 Redis")

        # 加载抢购库存（从 flash_sale 表）
        from app.models.flash_sale import FlashSale
        from datetime import datetime
        now = datetime.now()
        flash_sales = db.query(FlashSale).filter(
            FlashSale.end_time > now,
            FlashSale.status.in_(["未开始", "进行中"])
        ).all()
        for fs in flash_sales:
            key = f"{FLASH_STOCK_PREFIX}{fs.id}"
            if not redis_client.exists(key):
                redis_client.set(key, fs.flash_stock)
        logger.info(f"[Stock] 已初始化 {len(flash_sales)} 个抢购库存到 Redis")
    except Exception as e:
        logger.error(f"[Stock] init_stock 失败: {e}")
    finally:
        db.close()


def deduct_stock(gift_id: int, quantity: int = 1) -> tuple:
    """
    Redis DECR 原子扣减礼品库存。
    返回: (success: bool, remaining: int)
    扣到负数则回滚 INCR。
    """
    key = f"{GIFT_STOCK_PREFIX}{gift_id}"
    try:
        # Lua 脚本保证原子性：扣减后若 >=0 则成功，否则回滚
        lua_script = """
        local key = KEYS[1]
        local qty = tonumber(ARGV[1])
        local current = redis.call('GET', key)
        if not current then
            return -2  -- key 不存在
        end
        current = tonumber(current)
        if current < qty then
            return -1  -- 库存不足
        end
        local after = redis.call('DECRBY', key, qty)
        return after
        """
        result = redis_client.eval(lua_script, 1, key, quantity)
        if result == -2:
            logger.warning(f"[Stock] 礼品 {gift_id} 库存 key 不存在")
            return False, 0
        if result == -1:
            logger.warning(f"[Stock] 礼品 {gift_id} 库存不足")
            return False, 0
        logger.info(f"[Stock] 礼品 {gift_id} 扣减 {quantity}，剩余 {result}")
        return True, int(result)
    except Exception as e:
        logger.error(f"[Stock] deduct_stock 失败: {e}")
        return False, 0


def deduct_flash_stock(flash_sale_id: int, quantity: int = 1) -> tuple:
    """
    Redis DECR 原子扣减抢购库存。
    返回: (success: bool, remaining: int)
    """
    key = f"{FLASH_STOCK_PREFIX}{flash_sale_id}"
    try:
        lua_script = """
        local key = KEYS[1]
        local qty = tonumber(ARGV[1])
        local current = redis.call('GET', key)
        if not current then
            return -2
        end
        current = tonumber(current)
        if current < qty then
            return -1
        end
        local after = redis.call('DECRBY', key, qty)
        return after
        """
        result = redis_client.eval(lua_script, 1, key, quantity)
        if result == -2:
            return False, 0
        if result == -1:
            return False, 0
        logger.info(f"[Stock] 抢购 {flash_sale_id} 扣减 {quantity}，剩余 {result}")
        return True, int(result)
    except Exception as e:
        logger.error(f"[Stock] deduct_flash_stock 失败: {e}")
        return False, 0


def restore_stock(gift_id: int, quantity: int = 1):
    """回补 Redis 库存"""
    key = f"{GIFT_STOCK_PREFIX}{gift_id}"
    try:
        redis_client.incrby(key, quantity)
    except Exception as e:
        logger.error(f"[Stock] restore_stock 失败: {e}")


def restore_flash_stock(flash_sale_id: int, quantity: int = 1):
    """回补抢购 Redis 库存"""
    key = f"{FLASH_STOCK_PREFIX}{flash_sale_id}"
    try:
        redis_client.incrby(key, quantity)
    except Exception as e:
        logger.error(f"[Stock] restore_flash_stock 失败: {e}")


def sync_to_db():
    """将 Redis 礼品库存批量写回 MySQL gift 表"""
    db = SessionLocal()
    try:
        gifts = db.query(Gift).filter(Gift.status == "上架").all()
        updated = 0
        for gift in gifts:
            key = f"{GIFT_STOCK_PREFIX}{gift.id}"
            redis_val = redis_client.get(key)
            if redis_val is not None:
                redis_stock = int(redis_val)
                if redis_stock != gift.stock:
                    gift.stock = redis_stock
                    updated += 1
        if updated > 0:
            db.commit()
        logger.info(f"[Stock] sync_to_db 完成，更新 {updated} 个礼品库存")
    except Exception as e:
        logger.error(f"[Stock] sync_to_db 失败: {e}")
        db.rollback()
    finally:
        db.close()
