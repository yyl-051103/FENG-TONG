<template>
  <nav class="navbar">
    <div class="logo">🛡️ 智能风控新闻平台</div>
    <div class="nav-links">
      <router-link to="/" :class="{ active: isActive('/') }">🏠 首页</router-link>
      <router-link to="/search" :class="{ active: isActive('/search') }">🔍 搜索</router-link>
      <router-link to="/map" :class="{ active: isActive('/map') }">🗺️ 地图</router-link>
      <router-link to="/flash-sale" :class="{ active: isActive('/flash-sale') }">⚡ 抢购</router-link>
      <router-link to="/news/create" :class="{ active: isActive('/news/create') }">✍️ 创作</router-link>
      <router-link to="/news/my" :class="{ active: isActive('/news/my') }">📰 我的发布</router-link>
      <router-link to="/gifts" :class="{ active: isActive('/gifts') }">🎁 礼品</router-link>
      <router-link to="/orders" :class="{ active: isActive('/orders') }">📦 订单</router-link>
      <router-link to="/profile" :class="{ active: isActive('/profile') }">👤 个人中心</router-link>
      <router-link v-if="userStore.isAdmin" to="/admin" :class="{ active: isActive('/admin') }">🔧 管理</router-link>
    </div>
    <div class="user-info">
      <router-link to="/score" class="score-badge" title="查看积分明细">
        💰 积分: {{ userStore.userInfo?.score_balance ?? 0 }}
      </router-link>
      <div class="user-avatar">{{ avatarChar }}</div>
      <span>{{ displayName }}</span>
      <button class="logout-btn" @click="doLogout">退出</button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, watch, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 每次路由切换时刷新用户信息（确保积分实时同步）
watch(() => route.path, () => {
  userStore.fetchUserInfo();
});
onMounted(() => {
  userStore.fetchUserInfo();
});

const avatarChar = computed(() =>
  (userStore.userInfo?.nickname || userStore.userInfo?.username || "U")
    .charAt(0)
    .toUpperCase()
);
const displayName = computed(
  () => userStore.userInfo?.nickname || userStore.userInfo?.username || "用户"
);

function isActive(path: string) {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}

function doLogout() {
  userStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.navbar {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 14px 28px;
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow);
  backdrop-filter: blur(12px);
}
.logo {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-links {
  display: flex;
  gap: 8px;
  align-items: center;
}
.nav-links a {
  text-decoration: none;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  transition: all 0.3s;
  font-weight: 500;
  font-size: 14px;
}
.nav-links a:hover,
.nav-links a.active {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}
.score-badge {
  padding: 4px 12px;
  border-radius: 20px;
  background: linear-gradient(135deg, #fff8e1, #ffecb3);
  color: #f57f17;
  font-weight: 700;
  font-size: 13px;
  text-decoration: none;
  transition: all 0.3s;
  border: 1px solid #ffe082;
  white-space: nowrap;
}
.score-badge:hover {
  background: linear-gradient(135deg, #ffecb3, #ffe082);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.2);
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}
.logout-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}
.logout-btn:hover {
  background: #ffebee;
  color: #c62828;
  border-color: #ffcdd2;
}
@media (max-width: 768px) {
  .navbar {
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style>
