/**
 * 认证 API 封装
 */
import request from "./request";

export interface LoginParams {
  username: string;
  password: string;
}

export interface RegisterParams {
  username: string;
  password: string;
  role?: string;
  nickname?: string;
  phone: string;
  sms_code: string;
  invite_code?: string;
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  nickname: string | null;
  phone?: string | null;
  score_balance?: number;
}

export interface SendSmsParams { phone: string }
export interface PhoneLoginParams { phone: string; sms_code: string }
export interface ChangePhoneParams { phone: string; sms_code: string }

export const authApi = {
  login(params: LoginParams) {
    return request.post("/api/auth/login", params);
  },

  register(params: RegisterParams) {
    return request.post("/api/auth/register", params);
  },

  logout() {
    return request.post("/api/auth/logout");
  },

  getMe() {
    return request.get<{ code: number; data: UserInfo }>("/api/auth/me");
  },

  refresh(refreshToken: string) {
    return request.post("/api/auth/refresh", { refresh_token: refreshToken });
  },

  sendSms(params: SendSmsParams) {
    return request.post("/api/auth/send-sms", params);
  },

  phoneLogin(params: PhoneLoginParams) {
    return request.post("/api/auth/phone-login", params);
  },

  changePhone(params: ChangePhoneParams) {
    return request.put("/api/auth/change-phone", params);
  },
};
