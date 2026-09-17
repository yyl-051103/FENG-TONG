/**
 * 新闻相关 API 封装
 */
import request from "./request";

export interface PublishParams {
  title: string;
  content: string;
  source?: string;
  location?: string;
}

export interface AIAssistParams {
  original_content: string;
  assist_type: string;
  title?: string;
}

export const newsApi = {
  /** 发布新闻 */
  publish(params: PublishParams) {
    return request.post("/api/news/publish", params, { timeout: 90000 });
  },

  /** 新闻列表（首页） */
  list() {
    return request.get("/api/news/list");
  },

  /** 新闻详情 */
  detail(id: number) {
    return request.get(`/api/news/detail/${id}`);
  },

  /** 删除新闻 */
  delete(id: number) {
    return request.delete(`/api/news/${id}`);
  },

  /** 我的发布 */
  my() {
    return request.get("/api/news/my");
  },

  /** 点赞切换 */
  toggleLike(newsId: number) {
    return request.post(`/api/news/${newsId}/like`);
  },

  /** 收藏切换 */
  toggleFavorite(newsId: number) {
    return request.post(`/api/news/${newsId}/favorite`);
  },

  /** 获取评论列表 */
  getComments(newsId: number) {
    return request.get(`/api/news/${newsId}/comments`);
  },

  /** 发表评论 */
  postComment(newsId: number, content: string) {
    return request.post(`/api/news/${newsId}/comment`, null, {
      params: { content },
    });
  },

  /** 获取交互统计 */
  getStats(newsId: number) {
    return request.get(`/api/news/${newsId}/stats`);
  },

  /** 获取收藏列表 */
  getFavorites() {
    return request.get("/api/user/favorites");
  },

  // ── AI 助手 ──

  /** AI 创作辅助 */
  aiAssist(params: AIAssistParams) {
    return request.post("/api/ai/assist", params, { timeout: 90000 });
  },

  /** 个人 AI 记录 */
  aiRecords() {
    return request.get("/api/ai/record");
  },

  /** 删除 AI 记录 */
  deleteAiRecord(id: number) {
    return request.delete(`/api/ai/record/${id}`);
  },

  // ── 管理员 ──

  /** 全部新闻 */
  adminNews() {
    return request.get("/api/admin/news");
  },

  /** 审核新闻 */
  reviewNews(newsId: number, status: string) {
    return request.put(`/api/admin/news/${newsId}/review`, null, {
      params: { status },
    });
  },

  /** 用户统计 */
  adminUserStats() {
    return request.get("/api/admin/user/stats");
  },

  /** 全部 AI 记录 */
  adminAiRecords() {
    return request.get("/api/admin/ai/records");
  },
};
