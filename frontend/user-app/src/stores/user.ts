/**
 * Pinia 用户状态管理（localStorage 持久化）
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authApi, type UserInfo } from "../api/auth";

const STORAGE_KEY = "fengtong-user";

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

function saveState(state: { accessToken: string; refreshToken: string; userInfo: UserInfo | null }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const useUserStore = defineStore("user", () => {
  const saved = loadState();

  const accessToken = ref<string>(saved.accessToken || "");
  const refreshToken = ref<string>(saved.refreshToken || "");
  const userInfo = ref<UserInfo | null>(saved.userInfo || null);

  const isLoggedIn = computed(() => !!accessToken.value);
  const isAdmin = computed(() => userInfo.value?.role === "admin");

  function persist() {
    saveState({
      accessToken: accessToken.value,
      refreshToken: refreshToken.value,
      userInfo: userInfo.value,
    });
  }

  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    persist();
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password });
    const data = res.data;
    accessToken.value = data.access_token;
    refreshToken.value = data.refresh_token;
    userInfo.value = data.user;
    persist();
  }

  async function phoneLogin(phone: string, smsCode: string) {
    const res = await authApi.phoneLogin({ phone, sms_code: smsCode });
    const data = res.data;
    accessToken.value = data.access_token;
    refreshToken.value = data.refresh_token;
    userInfo.value = data.user;
    persist();
  }

  async function register(
    username: string,
    password: string,
    role = "user",
    nickname = "",
    phone = "",
    smsCode = "",
    inviteCode = ""
  ) {
    await authApi.register({ username, password, role, nickname, phone, sms_code: smsCode, invite_code: inviteCode });
  }

  async function fetchUserInfo() {
    if (!accessToken.value) return;
    try {
      const res = await authApi.getMe();
      userInfo.value = res.data.data;
      persist();
    } catch {
      logout();
    }
  }

  function updateScoreBalance(newBalance: number) {
    if (userInfo.value) {
      userInfo.value.score_balance = newBalance;
      persist();
    }
  }

  async function logout() {
    if (accessToken.value) {
      try {
        await authApi.logout();
      } catch {}
    }
    accessToken.value = "";
    refreshToken.value = "";
    userInfo.value = null;
    persist();
  }

  return {
    accessToken,
    refreshToken,
    userInfo,
    isLoggedIn,
    isAdmin,
    setTokens,
    login,
    phoneLogin,
    register,
    fetchUserInfo,
    updateScoreBalance,
    logout,
    persist,
  };
});
