import request from "./request";

export const mapApi = {
  /** 区域统计（省级） */
  regionStats() {
    return request.get("/api/map/region-stats");
  },

  /** 子级统计 */
  childrenStats(level: string, parent: string) {
    return request.get("/api/map/children-stats", { params: { level, parent } });
  },

  /** 区域新闻列表 */
  regionNews(region: string) {
    return request.get("/api/map/region-news", { params: { region } });
  },

  /** 新闻标记点列表（已通过 + 有坐标） */
  newsMarkers() {
    return request.get("/api/map/news-markers");
  },
};
