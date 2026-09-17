/**
 * 支付宝 API
 */
import request from "./request";

export const alipayApi = {
  /** 获取授权URL */
  getAuthUrl() {
    return request.get<{ code: number; data: { auth_url: string } }>(
      "/api/alipay/auth-url"
    );
  },

  /** 授权回调 */
  callback(authCode: string, state?: string) {
    return request.post<{
      code: number;
      data: { alipay_user_id: string; access_token: string };
      message: string;
    }>("/api/alipay/callback", { auth_code: authCode, state: state || "" });
  },

  /** 生成扫码支付二维码 */
  prepay(orderNo: string) {
    return request.post<{
      code: number;
      data: { qr_code: string; order_no: string; total_price: number; already_paid?: boolean };
    }>("/api/alipay/prepay", { order_no: orderNo });
  },

  /** 查询订单支付状态 */
  queryOrderStatus(orderNo: string) {
    return request.get<{
      code: number;
      data: { order_no: string; status: string; total_price: number };
    }>(`/api/alipay/order-status/${orderNo}`);
  },
};
