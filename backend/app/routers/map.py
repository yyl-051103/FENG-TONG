"""
地图相关路由：区域统计 / 子级统计 / 区域新闻 / 新闻标记 / GeoJSON 代理
"""
import json
import os
import re
from collections import Counter
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import text
import httpx

from app.dependencies import get_db

router = APIRouter(prefix="/api/map", tags=["map"])

GEOJSON_CDN = "https://geo.datav.aliyun.com/areas_v3/bound/"


@router.get("/geojson/{adcode}")
def proxy_geojson(adcode: str):
    """
    代理阿里云 DataV GeoJSON，解决浏览器跨域问题。
    例如 /api/map/geojson/100000 -> https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
    """
    url = f"{GEOJSON_CDN}{adcode}_full.json"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, follow_redirects=True)
            resp.raise_for_status()
    except Exception as e:
        return Response(content=f"GeoJSON proxy error: {e}", status_code=502)

    return Response(
        content=resp.content,
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
        },
    )

# 加载坐标字典（启动时一次性加载）
_COORDS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "user-app", "public", "china-coords.json")
_coords_cache: dict | None = None


def _load_coords() -> dict:
    global _coords_cache
    if _coords_cache is not None:
        return _coords_cache
    try:
        with open(_COORDS_FILE, "r", encoding="utf-8") as f:
            _coords_cache = json.load(f)
    except Exception:
        _coords_cache = {}
    return _coords_cache


def _resolve_coords(location: str) -> tuple[float, float] | None:
    """将 location（省/市/区名）映射为经纬度。匹配策略：精确匹配 → 区名 → 市名 → 省名。"""
    if not location:
        return None
    coords = _load_coords()
    # 1. 精确匹配
    if location in coords:
        c = coords[location]
        return (c[0], c[1])
    # 2. 尝试在 location 中匹配区名
    for name in coords:
        if len(name) >= 4 and name in location:
            c = coords[name]
            return (c[0], c[1])
    # 3. 兜底：取 location 前几个字尝试匹配
    for name in coords:
        if len(name) >= 3 and name[:3] in location:
            c = coords[name]
            return (c[0], c[1])
    return None


def extract_province(location: str) -> str | None:
    """从 location 提取省级地名。"""
    if not location:
        return None
    m = re.match(r"([\u4e00-\u9fff]+?(?:省|自治区|特别行政区|市))", location)
    if m:
        return m.group(1)
    # 兜底：取前3个字
    return location[:3] if len(location) >= 2 else location


def extract_city(location: str, province: str) -> str | None:
    """在给定省级地名下提取市级地名。"""
    if not location or not province:
        return None
    if not location.startswith(province):
        return None
    rest = location[len(province) :]
    if not rest:
        return province  # 直辖市：省级=市级
    m = re.match(r"([\u4e00-\u9fff]+?(?:市|州|地区|盟))", rest)
    if m:
        return m.group(1)
    return rest[:3] if len(rest) >= 3 else rest


def extract_district(location: str, parent: str) -> str | None:
    """在给定市级或省级地名下提取区级地名。"""
    if not location or not parent:
        return None
    idx = location.find(parent)
    if idx == -1:
        return None
    rest = location[idx + len(parent) :]
    if not rest:
        return None
    m = re.match(r"([\u4e00-\u9fff]+?(?:区|县|市))", rest)
    if m:
        return m.group(1)
    return rest[:3] if len(rest) >= 3 else rest


def _fetch_locations(db) -> list[str]:
    rows = db.execute(
        text(
            "SELECT location FROM news "
            "WHERE status IN ('approved', '已通过') AND location IS NOT NULL AND location != ''"
        )
    ).fetchall()
    return [r[0] for r in rows]


@router.get("/region-stats")
def region_stats(db=Depends(get_db)):
    """按省份统计新闻数量（从 location 字段提取）。"""
    locations = _fetch_locations(db)
    counter: Counter = Counter()
    for loc in locations:
        p = extract_province(loc)
        if p:
            counter[p] += 1
    return [{"name": k, "value": v} for k, v in counter.most_common()]


@router.get("/children-stats")
def children_stats(
    level: str = Query("city", description="子级类型: city|district"),
    parent: str = Query(..., description="父级地名，如 广东省"),
    db=Depends(get_db),
):
    """
    获取指定父级下的子级统计。
    level=city, parent=广东省 → 返回广东省下各市的新闻数量
    level=district, parent=广州市 → 返回广州市下各区的新闻数量
    """
    locations = _fetch_locations(db)
    counter: Counter = Counter()
    for loc in locations:
        if parent not in loc:
            continue
        child = None
        if level == "city":
            child = extract_city(loc, parent)
        elif level == "district":
            child = extract_district(loc, parent)
        if child:
            counter[child] += 1
    return [{"name": k, "value": v} for k, v in counter.most_common()]


@router.get("/region-news")
def region_news(
    region: str = Query(..., description="地区名（省/市/区皆可）"),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """获取指定地区的新闻列表（location 模糊匹配）。"""
    rows = db.execute(
        text(
            """SELECT id, title, source, create_time, latitude, longitude, location
               FROM news
               WHERE status IN ('approved', '已通过') AND location LIKE :pattern
               ORDER BY create_time DESC
               LIMIT :limit"""
        ),
        {"pattern": f"%{region}%", "limit": limit},
    ).fetchall()
    return [
        {
            "id": row[0],
            "title": row[1],
            "source": row[2],
            "create_time": row[3].isoformat() if row[3] else None,
            "latitude": row[4],
            "longitude": row[5],
            "location": row[6],
        }
        for row in rows
    ]


@router.get("/news-markers")
def news_markers(db=Depends(get_db)):
    """返回所有已通过且有经纬度坐标的新闻标记点列表，坐标直接取自数据库。"""
    rows = db.execute(
        text(
            """SELECT id, title, location, latitude, longitude
               FROM news
               WHERE status IN ('approved', '已通过')
                 AND latitude IS NOT NULL
                 AND longitude IS NOT NULL
               ORDER BY create_time DESC"""
        )
    ).fetchall()
    markers = []
    for row in rows:
        markers.append({
            "id": row[0],
            "title": row[1],
            "location": row[2],
            "lat": row[3],
            "lng": row[4],
        })
    return markers
