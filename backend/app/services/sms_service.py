"""
阿里云号码认证服务 - 短信验证码发送与校验
"""
import os
import json
import random
import logging

from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
from alibabacloud_tea_util import models as util_models

from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

SIGN_NAME = "速通互联验证码"
TEMPLATE_LOGIN_REGISTER = "100001"
TEMPLATE_CHANGE_PHONE = "100002"


def _get_client() -> DypnsapiClient:
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    if not access_key_id or not access_key_secret:
        raise ValueError("ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET 未配置")
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )
    config.endpoint = 'dypnsapi.aliyuncs.com'
    return DypnsapiClient(config)


def _generate_code() -> str:
    return str(random.randint(100000, 999999))


def send_sms_code(phone: str, template_code: str) -> dict:
    """
    发送短信验证码
    返回: {"success": bool, "error": str | None}
    """
    r = redis_client

    # 60秒内不可重复发送
    rate_key = f"sms_rate:{phone}"
    if r.exists(rate_key):
        return {"success": False, "error": "验证码发送过于频繁，请60秒后再试"}

    code = _generate_code()

    try:
        client = _get_client()
        req = dypnsapi_models.SendSmsVerifyCodeRequest(
            phone_number=phone,
            sign_name=SIGN_NAME,
            template_code=template_code,
            template_param=json.dumps({"code": code, "min": "5"}),
        )
        resp = client.send_sms_verify_code_with_options(req, util_models.RuntimeOptions())
        logger.info(f"[SMS] send to {phone}, template={template_code}, code={code}, resp_code={resp.body.code}")

        if resp.body.code == "OK":
            # 存入Redis，5分钟有效
            r.setex(f"sms_code:{phone}", 300, code)
            # 60秒频率限制
            r.setex(rate_key, 60, "1")
            return {"success": True, "error": None}
        else:
            msg = resp.body.message or "短信发送失败"
            logger.error(f"[SMS] send failed: {msg}")
            return {"success": False, "error": msg}
    except Exception as e:
        import traceback
        full_detail = str(e)
        if hasattr(e, 'data') and isinstance(getattr(e, 'data', None), dict):
            full_detail = json.dumps(e.data, ensure_ascii=False)
        logger.error(f"[SMS] send failed: {full_detail}")
        logger.error(f"[SMS] traceback: {traceback.format_exc()}")
        return {"success": False, "error": full_detail}


def verify_sms_code(phone: str, code: str) -> bool:
    """校验短信验证码，成功返回True并删除Redis记录"""
    r = redis_client
    key = f"sms_code:{phone}"
    stored = r.get(key)
    if stored and stored == code:
        r.delete(key)
        return True
    return False
