/**
 * 礼品 API
 */
import request from "./request";

export interface GiftItem {
  id: number;
  name: string;
  description: string;
  image: string;
  points_required: number;
  price: number;
  stock: number;
  category: string;
  status: string;
  create_time: string;
}

export const giftApi = {
  /** 用户端：礼品列表 */
  list(category?: string) {
    return request.get<{ code: number; data: { items: GiftItem[] } }>("/api/gifts", {
      params: category ? { category } : {},
    });
  },

  /** 用户端：礼品详情 */
  detail(giftId: number) {
    return request.get<{ code: number; data: GiftItem }>(`/api/gifts/${giftId}`);
  },
};

/** 管理端礼品表单 */
export interface GiftForm {
  name: string;
  description: string;
  image: string;
  points_required: number;
  price: number;
  stock: number;
  category: string;
  status: string;
}

/** 管理端礼品列表响应 */
export interface GiftListResponse {
  code: number;
  data: { items: GiftItem[] };
}

export const giftAdminApi = {
  /** 管理端：礼品列表（含库存、状态） */
  list() {
    return request.get<GiftListResponse>("/api/admin/gifts");
  },

  /** 管理端：创建礼品 */
  create(data: GiftForm) {
    return request.post<{ code: number; data: GiftItem }>("/api/admin/gifts", data);
  },

  /** 管理端：编辑礼品 */
  update(giftId: number, data: GiftForm) {
    return request.put<{ code: number; data: GiftItem }>(`/api/admin/gifts/${giftId}`, data);
  },

  /** 管理端：删除礼品 */
  delete(giftId: number) {
    return request.delete<{ code: number }>(`/api/admin/gifts/${giftId}`);
  },
};
