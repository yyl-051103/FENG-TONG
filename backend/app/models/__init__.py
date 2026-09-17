
from app.models.news import News, Comment, LikeRecord, FavoriteRecord
from app.models.ai_record import AICreationRecord
from app.models.score import ScoreRecord
from app.models.gift import Gift
from app.models.order import Order, OrderItem
from app.models.flash_sale import FlashSale

__all__ = ["User", "News", "Comment", "LikeRecord", "FavoriteRecord", "AICreationRecord", "ScoreRecord", "Gift", "Order", "OrderItem", "FlashSale"]

from app.models.user import User
