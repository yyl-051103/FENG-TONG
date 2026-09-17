<template>
<div class="page-container">
<NavBar />

<div class="card">
<div class="card-title"><span>📰</span> 我的发布记录</div>
<div v-if="alertMsg" class="alert alert-danger">{{ alertMsg }}</div>
<div v-if="loading" class="loading-wrap">
<div class="spinner"></div>
<div>正在加载...</div>
</div>
<div v-else-if="!newsList.length" class="empty-state">
<div class="empty-icon">📭</div>
<h3>暂无发布记录</h3>
<p>您还没有发布过新闻</p>
<br><router-link to="/news/create" class="btn btn-primary">去创作一篇</router-link>
</div>
<div v-else class="news-grid">
<div v-for="n in newsList" :key="n.id" class="news-card" @click="goDetail(n.id)">
<div class="news-title">{{ n.title }}</div>
<div class="news-content">{{ n.content }}</div>
<div class="news-meta">
<span class="news-source-tag">{{ n.source || '未知来源' }}</span>
<span>{{ formatTime(n.create_time) }}</span>
</div>
<div style="margin-top:10px; display:flex; gap:6px;">
<span :class="['status-badge', n.status==='已通过'?'status-pass':n.status==='待审核'?'status-pending':'status-reject']">{{ n.status }}</span>
<span v-if="n.risk_level" :class="['status-badge', n.risk_level==='高'?'risk-high':n.risk_level==='中'?'risk-medium':'risk-low']">{{ n.risk_level }}风险</span>
</div>
<div style="margin-top:10px;">
<button class="btn btn-danger" style="padding:6px 14px; font-size:13px;" @click.stop="deleteNews(n.id)">删除</button>
</div>
</div>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import NavBar from "../components/NavBar.vue";
import { newsApi } from "../api/news";

const router = useRouter();

const loading = ref(true);
const newsList = ref<any[]>([]);
const alertMsg = ref("");

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
}

function showAlert(msg: string) {
  alertMsg.value = msg;
  setTimeout(() => { alertMsg.value = ""; }, 5000);
}

async function loadNews() {
  loading.value = true;
  try {
    const res = await newsApi.my();
    newsList.value = res.data || [];
  } catch (err: any) {
    showAlert("加载失败：" + (err.response?.data?.detail || err.message));
    newsList.value = [];
  } finally {
    loading.value = false;
  }
}

async function deleteNews(id: number) {
  if (!confirm("确定删除这条新闻吗？删除后不可恢复。")) return;
  try {
    await newsApi.delete(id);
    await loadNews();
  } catch (err: any) {
    showAlert("删除失败：" + (err.response?.data?.detail || err.message));
  }
}

function goDetail(id: number) {
  router.push(`/news/${id}`);
}

onMounted(() => {
  loadNews();
});
</script>

<style scoped>

.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.card-title {
  font-size: 20px; font-weight: 700;
  margin-bottom: 20px; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px;
}
.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}
.news-card {
  background: var(--surface);
  border-radius: var(--radius-sm);
  padding: 22px;
  border: 1px solid var(--border);
  transition: all 0.35s ease;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(33,150,243,0.06);
}
.news-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
  border-color: var(--primary-light);
}
.news-title {
  font-size: 17px; font-weight: 700;
  color: var(--text-primary); margin-bottom: 10px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.news-content {
  font-size: 14px; color: var(--text-secondary);
  line-height: 1.6; margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.news-meta {
  display: flex; justify-content: space-between;
  align-items: center; font-size: 13px; color: var(--text-muted);
}
.news-source-tag {
  background: var(--primary-bg); color: var(--primary-dark);
  padding: 3px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.status-badge {
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 700;
}
.status-pass { background: #e8f5e9; color: #2e7d32; }
.status-pending { background: #fff8e1; color: #f57f17; }
.status-reject { background: #ffebee; color: #c62828; }
.risk-high { background: #ef5350; color: white; }
.risk-medium { background: #ffca28; color: #5d4037; }
.risk-low { background: #66bb6a; color: white; }
.empty-state {
  text-align: center; padding: 80px 20px; color: var(--text-muted);
}
.empty-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.4; }
.btn {
  padding: 10px 20px; border: none; border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s;
}
.btn-primary {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
}
.btn-primary:hover {
  transform: translateY(-2px); box-shadow: 0 4px 12px rgba(33,150,243,0.4);
}
.btn-danger { background: #ffebee; color: #c62828; }
.btn-danger:hover { background: #ffcdd2; }
.loading-wrap { text-align: center; padding: 60px; color: var(--primary); }
.spinner {
  display: inline-block; width: 36px; height: 36px;
  border: 3px solid rgba(33,150,243,0.15); border-radius: 50%;
  border-top-color: var(--primary); animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.alert {
  padding: 14px 18px; border-radius: var(--radius-sm);
  margin-bottom: 20px; border-left: 4px solid;
}
.alert-danger { background: #ffebee; color: #c62828; border-color: #ef5350; }
@media (max-width: 768px) {
  .news-grid { grid-template-columns: 1fr; }
}
</style>
