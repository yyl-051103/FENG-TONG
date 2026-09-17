"""
认证路由 - 注册 / 登录 / 退出 / 当前用户 / 刷新令牌
"""
import hmac
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    TokenResponse,
)
from app.utils.security import (
    hash_password,
    hash_password_sha256,
    verify_password,
    generate_token_str,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.utils.redis_client import add_active_session, remove_session, redis_client
from app.config import ADMIN_INVITE_CODE, JWT_EXPIRE_MINUTES
from app.services.sms_service import send_sms_code, verify_sms_code, TEMPLATE_LOGIN_REGISTER, TEMPLATE_CHANGE_PHONE
from app.schemas.auth import SendSmsRequest, PhoneLoginRequest, ChangePhoneRequest

router = APIRouter()


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 管理员注册需要邀请码验证
    if req.role == "admin" and (
        not ADMIN_INVITE_CODE
        or ADMIN_INVITE_CODE.startswith("CHANGE_ME_")
        or not hmac.compare_digest(req.invite_code or "", ADMIN_INVITE_CODE)
    ):
        raise HTTPException(status_code=400, detail="邀请码错误，无法注册为管理员")

    # 注册时使用 bcrypt 哈希，同时兼容原始 SHA-256 的 token 字段
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        nickname=req.nickname,
        token=generate_token_str(),  # 过渡期保留
        phone=req.phone,
    )
    db.add(user)
    db.commit()
    return {"code": 200, "msg": "注册成功"}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户名密码登录，返回 JWT"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="账号或密码错误")

    # 先用 bcrypt 验证，失败则回退到原始 SHA-256
    if not verify_password(req.password, user.password_hash):
        # 如果是老用户（SHA-256），登录成功后自动升级为 bcrypt
        old_hash = hash_password_sha256(req.password)
        if user.password_hash != old_hash:
            raise HTTPException(status_code=401, detail="账号或密码错误")
        # 升级密码哈希
        user.password_hash = hash_password(req.password)

    jti = uuid.uuid4().hex
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "jti": jti
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    add_active_session(jti)

    # 过渡期：更新数据库 token 字段
    user.token = generate_token_str()
    db.commit()

    return {
        "code": 200,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "nickname": user.nickname,
            "phone": user.phone,
        },
    }


@router.post("/logout")
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    """退出登录，移除 Redis 会话"""
    # 提取 jti 并移除会话
    token = authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if token:
        payload = verify_token(token)
        if payload:
            jti = payload.get("jti", "")
            if jti:
                remove_session(jti)

    # 过渡期：清空数据库 token
    user.token = None
    db.commit()

    return {"code": 200, "msg": "退出成功"}


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    real_user = db.query(User).filter(User.id == user.id).first()
    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "role": real_user.role if real_user else user.role,
            "nickname": user.nickname,
            "phone": real_user.phone if real_user else None,
            "score_balance": real_user.score_balance if real_user else 0,
        },
    }


@router.post("/refresh")
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """使用 refresh_token 换取新 access_token"""
    payload = verify_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的 refresh_token")

    jti_old = payload.get("jti", "")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    jti = uuid.uuid4().hex
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "jti": jti
    }

    access_token = create_access_token(token_data)
    refresh_token_new = create_refresh_token(token_data)

    if jti_old:
        remove_session(jti_old)
    add_active_session(jti)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_new,
        "token_type": "bearer",
    }

@router.post("/send-sms")
def send_sms(req: SendSmsRequest):
    """发送短信验证码（登录/注册通用）"""
    result = send_sms_code(req.phone, TEMPLATE_LOGIN_REGISTER)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"code": 200, "msg": "验证码已发送"}


@router.post("/phone-login")
def phone_login(req: PhoneLoginRequest, db: Session = Depends(get_db)):
    """手机号验证码登录"""
    if not verify_sms_code(req.phone, req.sms_code):
        raise HTTPException(status_code=400, detail="验证码错误")

    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        raise HTTPException(status_code=400, detail="该手机号尚未注册")

    jti = uuid.uuid4().hex
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "jti": jti,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    add_active_session(jti)
    user.token = generate_token_str()
    db.commit()

    return {
        "code": 200,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "nickname": user.nickname,
            "phone": user.phone,
        },
    }


@router.put("/change-phone")
def change_phone(
    req: ChangePhoneRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改/绑定手机号"""
    if not verify_sms_code(req.phone, req.sms_code):
        raise HTTPException(status_code=400, detail="验证码错误")

    # 从数据库获取真实持久化对象（get_current_user 返回的是 detached 对象）
    real_user = db.query(User).filter(User.id == user.id).first()
    if not real_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查手机号是否已被他人占用
    existing = db.query(User).filter(User.phone == req.phone, User.id != user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该手机号已被其他账号绑定")

    real_user.phone = req.phone
    db.commit()
    return {"code": 200, "msg": "手机号修改成功", "phone": req.phone}
