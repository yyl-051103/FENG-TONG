<template>
  <div class="favorites-wrapper">
    <div class="page-container">
      <NavBar />
      <div class="page-header">
        <h1>⭐ 我的收藏</h1>
        <span class="count-badge">共 {{ favorites.length }} 条收藏</span>
      </div>
      <div class="favorites-list">
        <div v-if="!favorites.length" class="empty-state">暂无收藏的新闻</div>
        <div v-for="item in favorites" :key="(item.news || item).id || item.id" class="fav-item">
          <router-link :to="'/news/' + ((item.news || item).id)" class="fav-title">
            {{ (item.news || item).title || '无标题' }}
          </router-link>
          <div class="fav-meta">
            <span>收藏时间：{{ formatTime(item.create_time) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { newsApi } from "../api/news";
import NavBar from "../components/NavBar.vue";

const favorites = ref<any[]>([]);

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

onMounted(async () => {
  try {
    const res = await newsApi.getFavorites();
    favorites.value = res.data || [];
  } catch {
    favorites.value = [];
  }
});
</script>

<style scoped>
.favorites-wrapper {
  background: linear-gradient(180deg, #e8f4fd 100%);
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 32px 40px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  color: white;
  box-shadow: var(--shadow-hover);
}
.page-header h1 {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
}
.count-badge {
  padding: 4px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}
.favorites-list {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.fav-item {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  transition: all 0.2s;
  border-radius: var(--radius-sm);
}
.fav-item:hover {
  background: var(--primary-bg);
}
.fav-item:last-child {
  border-bottom: none;
}
.fav-title {
  font-weight: 600;
  color: var(--primary-dark);
  font-size: 15px;
  margin-bottom: 6px;
  cursor: pointer;
  text-decoration: none;
  display: block;
}
.fav-title:hover {
  text-decoration: underline;
}
.fav-meta {
  font-size: 12px;
  color: var(--text-muted);
}
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
  font-size: 15px;
}
@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
