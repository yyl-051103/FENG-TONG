/**
 * Axios 实例 — baseURL + JWT 拦截器
 */
import axios from "axios";
import { useUserStore } from "../stores/user";
import router from "../router";

const request = axios.create({
  baseURL: "/",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器 — 自动附加 Bearer token
request.interceptors.request.use(
  (config) => {
    const store = useUserStore();
    if (store.accessToken) {
      config.headers.Authorization = `Bearer ${store.accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 — 401 时自动尝试 refresh（防竞态锁）
let refreshPromise: Promise<string> | null = null;

request.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== "/api/auth/refresh" &&
      originalRequest.url !== "/api/auth/logout"
    ) {
      // 若已有 refresh 正在进行中，排队等待而非独立发起
      if (refreshPromise) {
        try {
          const newToken = await refreshPromise;
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return request(originalRequest);
        } catch {
          return Promise.reject(error);
        }
      }

      originalRequest._retry = true;
      const store = useUserStore();

      refreshPromise = (async () => {
        try {
          const res = await axios.post("/api/auth/refresh", {
            refresh_token: store.refreshToken,
          });
          const { access_token, refresh_token } = res.data;
          store.setTokens(access_token, refresh_token);
          return access_token;
        } catch {
          store.accessToken = "";
          store.refreshToken = "";
          store.userInfo = null;
          localStorage.removeItem("fengtong-user");
          router.replace("/login");
          throw error;
        } finally {
          refreshPromise = null;
        }
      })();

      try {
        const newToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return request(originalRequest);
      } catch {
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export default request;
