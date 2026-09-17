"""
FastAPI 入口 — 创建表 + 健康检查 + CORS + 路由注册
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.config import CORS_ORIGINS

# 导入所有模型以触发 Base 元数据注册
from app.models import User, News, Comment, LikeRecord, FavoriteRecord, AICreationRecord, Gift, Order, OrderItem, FlashSale  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭生命周期"""
    # 启动时
    Base.metadata.create_all(bind=engine)
    from app.services.search_service import init_index
    from app.services.score_consumer import start_score_consumer
    from app.services.order_consumer import start_order_consumer
    from app.services.stock import init_stock
    from app.services.order_timeout_scanner import start_timeout_scanner

    await init_index()
    start_score_consumer()
    start_order_consumer()
    start_timeout_scanner()
    init_stock()
    yield
    # 关闭时

app = FastAPI(title="智能风控新闻发布平台", version="0.5.0", lifespan=lifespan)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "fengtong-backend"}


# ── 路由注册 ──
from app.routers import auth, news, ai, admin, user, score, search as search_router
from app.routers import gift as gift_router
from app.routers import gift_admin as gift_admin_router
from app.routers import order as order_router
from app.routers import flash_sale as flash_sale_router
from app.routers import flash_sale_admin as flash_sale_admin_router
from app.routers import map as map_router
from app.routers import alipay as alipay_router

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(news.router, prefix="/api/news", tags=["新闻"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI助手"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(score.router)
app.include_router(search_router.router)
app.include_router(gift_router.router)
app.include_router(gift_admin_router.router)
app.include_router(order_router.router)
app.include_router(flash_sale_router.router)
app.include_router(flash_sale_admin_router.router)
app.include_router(alipay_router.router)
app.include_router(map_router.router)
