/**
 * 订单 API
 */
import request from "./request";

export interface OrderItemDetail {
  gift_id?: number;
  gift_name: string;
  quantity: number;
  points_per_item: number;
  price_per_item: number;
}

export interface OrderData {
  id: number;
  order_no: string;
  total_points: number;
  total_price: number;
  status: string;
  create_time: string;
  expire_time?: string;
  items: OrderItemDetail[];
}

export interface CreateOrderResult {
  id: number;
  order_no: string;
  total_points: number;
  total_price: number;
  status: string;
  use_points: boolean;
}

export const orderApi = {
  /** 创建订单 */
  create(params: { gift_id: number; quantity: number; flash_sale_id?: number; use_points?: boolean }) {
    return request.post<{ code: number; data: CreateOrderResult; message: string }>(
      "/api/orders",
      params
    );
  },

  /** 用户订单列表 */
  list() {
    return request.get<{ code: number; data: { items: OrderData[] } }>("/api/orders");
  },

  /** 订单详情 */
  detail(orderId: number) {
    return request.get<{ code: number; data: OrderData }>(`/api/orders/${orderId}`);
  },

  /** 抢购排队结果 */
  getResult() {
    return request.get<{ code: number; data: { status: string; success?: boolean; order_no?: string; reason?: string } }>(
      "/api/orders/result"
    );
  },

  /** 取消订单 */
  cancel(orderId: number) {
    return request.put<{ code: number; message: string }>(`/api/orders/${orderId}/cancel`);
  },

  /** 删除订单 */
  delete(orderId: number) {
    return request.delete<{ code: number; message: string }>(`/api/orders/${orderId}`);
  },
};
