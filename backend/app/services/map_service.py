"""
百度地图地理编码服务
"""
import os
import logging
import aiohttp

logger = logging.getLogger(__name__)

BAIDU_AK = os.getenv("BAIDU_MAP_AK", "IJa9TznW5ZUFQ8ElzJeWuqX3iCOhNaI4")
BAIDU_GEOCODE_URL = "https://api.map.baidu.com/geocoding/v3"


async def geocode(address: str) -> dict | None:
    """
    地址 → 经纬度。返回 {"lat": float, "lng": float} 或 None
    """
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                BAIDU_GEOCODE_URL,
                params={"address": address, "ak": BAIDU_AK, "output": "json"},
            ) as resp:
                data = await resp.json(content_type=None)
                if data.get("status") != 0:
                    logger.warning(f"[Map] 地理编码失败: {data.get('message')} address={address}")
                    return None
                loc = data["result"]["location"]
                return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception as e:
        logger.error(f"[Map] 地理编码异常: {e}")
        return None
