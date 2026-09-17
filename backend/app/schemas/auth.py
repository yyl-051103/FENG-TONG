"""
认证相关的 Pydantic 请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    nickname: Optional[str] = ""
    phone: str
    sms_code: str
    invite_code: Optional[str] = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    code: int = 200
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    nickname: Optional[str] = None
    phone: Optional[str] = None


class MeResponse(BaseModel):
    code: int = 200
    data: UserInfo


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PhoneLoginRequest(BaseModel):
    phone: str
    sms_code: str


class SendSmsRequest(BaseModel):
    phone: str


class ChangePhoneRequest(BaseModel):
    phone: str
    sms_code: str
