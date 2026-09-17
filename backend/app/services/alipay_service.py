"""
支付宝沙箱服务 — OAuth 授权 + 支付 + 验签
"""
import os
import logging
import json
from alipay import AliPay

logger = logging.getLogger(__name__)

# 支付宝沙箱配置
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_PRIVATE_KEY_PATH = os.getenv("ALIPAY_PRIVATE_KEY_PATH", "secrets/alipay_private_key.pem")
ALIPAY_PUBLIC_KEY_PATH = os.getenv("ALIPAY_PUBLIC_KEY_PATH", "secrets/alipay_public_key.pem")
ALIPAY_GATEWAY = os.getenv("ALIPAY_GATEWAY", "https://openapi-sandbox.dl.alipaydev.com/gateway.do")
ALIPAY_REDIRECT_URI = os.getenv("ALIPAY_REDIRECT_URI", "http://localhost:5173/checkout/callback")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL", "http://localhost:8000/api/alipay/notify")

# 读取 PEM 文件
def _read_pem(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _get_alipay_client() -> AliPay:
    """获取支付宝沙箱客户端实例"""
    if not ALIPAY_APP_ID:
        raise RuntimeError("ALIPAY_APP_ID is not configured")
    if not os.path.isfile(ALIPAY_PRIVATE_KEY_PATH) or not os.path.isfile(ALIPAY_PUBLIC_KEY_PATH):
        raise RuntimeError("Alipay PEM files are missing; see README.md for secrets/ setup")
    return AliPay(
        appid=ALIPAY_APP_ID,
        app_notify_url=ALIPAY_NOTIFY_URL,
        app_private_key_string=_read_pem(ALIPAY_PRIVATE_KEY_PATH),
        alipay_public_key_string=_read_pem(ALIPAY_PUBLIC_KEY_PATH),
        sign_type="RSA2",
        debug=True,  # 沙箱模式
    )


def get_auth_url(state: str = "") -> str:
    """拼接 OAuth 授权 URL"""
    base = "https://openauth-sandbox.dl.alipaydev.com/oauth2/publicAppAuthorize.htm"
    params = f"app_id={ALIPAY_APP_ID}&scope=auth_user&redirect_uri={ALIPAY_REDIRECT_URI}"
    if state:
        params += f"&state={state}"
    return f"{base}?{params}"


def get_user_id(auth_code: str) -> dict:
    """
    用 auth_code 换取 access_token 和 user_id
    返回: {"success": bool, "user_id": str | None, "access_token": str | None, "error": str | None}
    """
    try:
        alipay = _get_alipay_client()
        result = alipay.server_api("alipay.system.oauth.token", auth_code=auth_code, grant_type="authorization_code")
        # result 格式: {"alipay_system_oauth_token_response": {"user_id": "xxx", "access_token": "xxx"}, "sign": "..."}
        if "alipay_system_oauth_token_response" in result:
            resp = result["alipay_system_oauth_token_response"]
            user_id = resp.get("user_id")
            access_token = resp.get("access_token")
            if user_id:
                return {"success": True, "user_id": user_id, "access_token": access_token, "error": None}
        return {"success": False, "user_id": None, "access_token": None, "error": "获取用户信息失败"}
    except Exception as e:
        logger.error(f"[Alipay] get_user_id 失败: {e}")
        return {"success": False, "user_id": None, "access_token": None, "error": str(e)}


def create_prepay(order_no: str, amount: float, subject: str) -> dict:
    """
    调用 alipay.trade.precreate 生成扫码支付二维码
    返回: {"qr_code": str, "order_no": str, "total_price": float}
    """
    try:
        alipay = _get_alipay_client()
        result = alipay.api_alipay_trade_precreate(
            out_trade_no=order_no,
            total_amount=str(round(amount, 2)),
            subject=subject,
            notify_url=ALIPAY_NOTIFY_URL,
        )
        # 记录完整响应以便排查
        logger.info(f"[Alipay] precreate 原始响应: {json.dumps(result, ensure_ascii=False)}")

        # SDK 可能返回两种格式:
        # A) {"alipay_trade_precreate_response": {"code": "10000", ...}}
        # B) {"code": "10000", "qr_code": "...", ...}   (直接解包)
        resp = result.get("alipay_trade_precreate_response") or result
        if resp.get("code") != "10000":
            err_msg = resp.get("sub_msg") or resp.get("msg") or "预下单失败"
            sub_code = resp.get("sub_code", "")
            code_detail = f"[{sub_code}] " if sub_code else ""
            raise Exception(f"{code_detail}{err_msg}")
        qr_code = resp.get("qr_code", "")
        if not qr_code:
            raise Exception("未获取到二维码")
        return {
            "qr_code": qr_code,
            "order_no": order_no,
            "total_price": amount,
        }
    except Exception as e:
        logger.error(f"[Alipay] create_prepay 失败: {e}")
        raise


def query_order(out_trade_no: str) -> bool:
    """
    主动查询支付宝订单支付状态（兜底异步通知不可达）。
    返回 True 表示已支付，False 表示未支付。
    """
    try:
        alipay = _get_alipay_client()
        result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
        logger.info(f"[Alipay] query 原始响应: {json.dumps(result, ensure_ascii=False)}")
        resp = result.get("alipay_trade_query_response") or result
        trade_status = resp.get("trade_status", "")
        return trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED")
    except Exception as e:
        logger.error(f"[Alipay] query_order 失败: {e}")
        return False


def verify_notify(data: dict, sign: str) -> bool:
    """验签支付宝异步通知"""
    try:
        alipay = _get_alipay_client()
        return alipay.verify(data, sign)
    except Exception as e:
        logger.error(f"[Alipay] verify_notify 失败: {e}")
        return False
