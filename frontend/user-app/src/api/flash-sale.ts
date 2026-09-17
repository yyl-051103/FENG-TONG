/**
 * 抢购 API
 */
import request from "./request";

export interface FlashSaleItem {
  id: number;
  gift_id: number;
  gift_name: string;
  gift_image: string;
  gift_description: string;
  flash_price_points: number;
  flash_price_cash: number;
  flash_stock: number;
  current_stock: number;
  /** Unix 时间戳（秒），由服务端返回 */
  start_time: number;
  /** Unix 时间戳（秒），由服务端返回 */
  end_time: number;
  /** ISO 字符串，仅用于展示 */
  start_time_str: string;
  /** ISO 字符串，仅用于展示 */
  end_time_str: string;
  status: string;
}

export interface FlashSaleAdminItem {
  id: number;
  gift_id: number;
  gift_name: string;
  flash_price_points: number;
  flash_price_cash: number;
  flash_stock: number;
  /** ISO 字符串，管理端返回 */
  start_time: string;
  /** ISO 字符串，管理端返回 */
  end_time: string;
  status: string;
  create_time: string;
}

export const flashSaleApi = {
  /** 用户端：获取进行中+即将开始的抢购列表 */
  list() {
    return request.get<{
      code: number;
      data: { items: FlashSaleItem[]; server_time: number };
    }>("/api/flash-sales");
  },
};

export const flashSaleAdminApi = {
  /** 管理端：全部抢购列表 */
  list() {
    return request.get<{
      code: number;
      data: { items: FlashSaleAdminItem[] };
    }>("/api/admin/flash-sales");
  },

  /** 创建抢购 */
  create(data: {
    gift_id: number;
    flash_price_points: number;
    flash_price_cash: number;
    flash_stock: number;
    start_time: string;
    end_time: string;
  }) {
    return request.post<{ code: number; data: any; message: string }>(
      "/api/admin/flash-sales",
      data
    );
  },

  /** 更新抢购 */
  update(
    id: number,
    data: Partial<{
      gift_id: number;
      flash_price_points: number;
      flash_price_cash: number;
      flash_stock: number;
      start_time: string;
      end_time: string;
      status: string;
    }>
  ) {
    return request.put<{ code: number; data: any; message: string }>(
      `/api/admin/flash-sales/${id}`,
      data
    );
  },

  /** 删除抢购 */
  delete(id: number) {
    return request.delete<{ code: number; message: string }>(
      `/api/admin/flash-sales/${id}`
    );
  },
};
