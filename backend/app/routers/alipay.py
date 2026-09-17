"""
支付宝路由 — OAuth 授权 + 支付 + 回调
"""
import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.order import Order
from app.services import alipay_service
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alipay", tags=["支付宝"])


class AuthCallbackRequest(BaseModel):
    auth_code: str
    state: Optional[str] = None


class PrepayRequest(BaseModel):
    order_no: str
    return_url: Optional[str] = ""


@router.get("/auth-url")
def get_auth_url():
    """获取支付宝 OAuth 授权 URL（无需登录，用于未登录用户通过支付宝授权登录）"""
    state = uuid.uuid4().hex
    url = alipay_service.get_auth_url(state=state)
    return {"code": 200, "data": {"auth_url": url}}


@router.post("/callback")
def alipay_callback(
    body: AuthCallbackRequest,
    db: Session = Depends(get_db),
):
    """OAuth 回调：用 auth_code 换 user_id。
    支付宝回跳时无 JWT token，通过 state 参数（user_id）反查用户。"""
    # state 参数中携带 user_id，用于识别用户
    user_id = None
    if body.state:
        try:
            user_id = int(body.state)
        except ValueError:
            pass

    result = alipay_service.get_user_id(body.auth_code)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "支付宝授权失败"))

    # 记录授权日志
    logger.info(f"[Alipay] user_id={user_id} 完成支付宝授权, alipay_user_id={result['user_id']}")

    return {
        "code": 200,
        "data": {
            "alipay_user_id": result["user_id"],
            "access_token": result["access_token"],
        },
        "message": "授权成功",
    }


@router.post("/prepay")
def prepay(
    body: PrepayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成扫码支付二维码 → 返回 qr_code"""
    order = db.query(Order).filter(Order.order_no == body.order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该订单")
    if order.status != "待支付":
        raise HTTPException(status_code=400, detail=f"订单状态为「{order.status}」，无法支付")

    amount = max(float(order.total_price) if order.total_price else 0.01, 0.01)  # 沙箱最低 0.01
    subject = "风瞳礼品兑换"

    # 下单前先主动查询：如果支付宝已支付但 DB 未同步，直接补同步并返回已支付
    alipay_paid = alipay_service.query_order(body.order_no)
    if alipay_paid:
        if order.status != "已支付":
            order.status = "已支付"
            redis_client.zrem("order:timeout", body.order_no)
            db.commit()
            logger.info(f"[Alipay] prepay 时发现订单 {body.order_no} 支付宝已支付，DB 状态已补同步")
        return {"code": 200, "data": {"already_paid": True, "order_no": body.order_no, "total_price": float(order.total_price) if order.total_price else 0.00}}

    try:
        result = alipay_service.create_prepay(
            order_no=body.order_no,
            amount=amount,
            subject=subject,
        )
        return {"code": 200, "data": result}
    except Exception as e:
        err_str = str(e)
        # TRADE_HAS_SUCCESS → 说明前一次支付已成功但未同步
        if "TRADE_HAS_SUCCESS" in err_str:
            order.status = "已支付"
            redis_client.zrem("order:timeout", body.order_no)
            db.commit()
            return {"code": 200, "data": {"already_paid": True, "order_no": body.order_no, "total_price": float(order.total_price) if order.total_price else 0.00}}
        raise HTTPException(status_code=500, detail=f"生成支付二维码失败: {err_str}")


@router.post("/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """接收支付宝异步通知 → 验签 → 更新订单状态"""
    try:
        form_data = await request.form()
        data = dict(form_data)

        sign = data.pop("sign", "")
        sign_type = data.pop("sign_type", "RSA2")

        # 验签
        if not alipay_service.verify_notify(data, sign):
            logger.warning(f"[Alipay] 验签失败: {data.get('out_trade_no')}")
            return "fail"

        trade_status = data.get("trade_status", "")
        out_trade_no = data.get("out_trade_no", "")

        if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            order = db.query(Order).filter(Order.order_no == out_trade_no).first()
            if order and order.status == "待支付":
                order.status = "已支付"
                redis_client.zrem("order:timeout", out_trade_no)
                db.commit()
                logger.info(f"[Alipay] 订单 {out_trade_no} 支付成功，状态已更新")

        return "success"
    except Exception as e:
        logger.error(f"[Alipay] notify 处理失败: {e}")
        return "fail"


@router.get("/order-status/{order_no}")
def query_order_status(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单支付状态（前端轮询用）。
    沙箱环境无法回调 localhost，因此当 DB 状态为待支付时，
    主动调用支付宝 trade.query 确认真实支付状态并同步更新 DB。
    """
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看")

    # DB 尚未标记为已支付 → 调用支付宝主动查询
    if order.status == "待支付":
        try:
            real_status = alipay_service.query_order(order_no)
            if real_status:
                order.status = "已支付"
                db.commit()
                logger.info(f"[Alipay] 主动查询发现订单 {order_no} 已支付，状态已同步")
        except Exception as e:
            logger.warning(f"[Alipay] 主动查询订单 {order_no} 失败: {e}")

    return {
        "code": 200,
        "data": {
            "order_no": order.order_no,
            "status": order.status,
            "total_price": float(order.total_price) if order.total_price else 0.00,
        },
    }
