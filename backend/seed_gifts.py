"""
种子数据 - 插入 2 条测试礼品数据（全部 0 积分 0 元）
"""
from app.database import SessionLocal, engine, Base
from app.models.gift import Gift

# 确保表存在
Base.metadata.create_all(bind=engine)

gifts_data = [
    {
        "name": "瑞兽麒麟·限定款",
        "description": "东方瑞兽麒麟造型，手工彩绘，限量发行500体。威严与祥瑞并存，守护您的桌面好运。",
        "image": "https://placehold.co/400x400/1a237e/ffffff?text=麒麟",
        "points_required": 0,
        "price": 0.00,
        "stock": 30,
        "category": "限定款",
        "status": "上架",
    },
    {
        "name": "敦煌飞天·联名款",
        "description": "敦煌研究院联名，飞天仙女飘逸姿态，还原壁画经典色彩，附赠收藏证书。",
        "image": "https://placehold.co/400x400/283593/ffffff?text=飞天",
        "points_required": 0,
        "price": 0.00,
        "stock": 20,
        "category": "联名款",
        "status": "上架",
    },
]

db = SessionLocal()
try:
    existing = db.query(Gift).count()
    if existing > 0:
        print(f"已有 {existing} 条礼品数据，跳过种子插入。")
    else:
        for data in gifts_data:
            gift = Gift(**data)
            db.add(gift)
        db.commit()
        print(f"已插入 {len(gifts_data)} 条礼品数据。")
finally:
    db.close()
