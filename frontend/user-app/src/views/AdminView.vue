<template>
<div class="page-container">
<NavBar />

<div class="admin-toolbar">
  <router-link to="/admin/gifts" class="toolbar-link">礼品管理</router-link>
  <router-link to="/admin/flash-sales" class="toolbar-link" style="background:linear-gradient(135deg,#ff6f00,#e65100);margin-left:8px;">抢购管理</router-link>
</div>

<div class="stats-grid">
<div class="stat-card"><div class="stat-icon">👥</div><div class="stat-num">{{ statUsers }}</div><div class="stat-label">总用户数</div></div>
<div class="stat-card"><div class="stat-icon">🔧</div><div class="stat-num">{{ statAdmins }}</div><div class="stat-label">管理员</div></div>
<div class="stat-card"><div class="stat-icon">📰</div><div class="stat-num">{{ statTotal }}</div><div class="stat-label">总新闻数</div></div>
<div class="stat-card"><div class="stat-icon">✅</div><div class="stat-num">{{ statPass }}</div><div class="stat-label">已通过</div></div>
<div class="stat-card"><div class="stat-icon">⏳</div><div class="stat-num">{{ statPending }}</div><div class="stat-label">待审核</div></div>
<div class="stat-card"><div class="stat-icon">❌</div><div class="stat-num">{{ statReject }}</div><div class="stat-label">已拒绝</div></div>
<div class="stat-card"><div class="stat-icon">💬</div><div class="stat-num">{{ statComments }}</div><div class="stat-label">总评论数</div></div>
<div class="stat-card"><div class="stat-icon">❤️</div><div class="stat-num">{{ statLikes }}</div><div class="stat-label">总点赞数</div></div>
</div>

<div class="main-grid">
<div class="card">
<div class="card-title"><span>📋</span> 新闻管理</div>
<div class="tab-bar">
<button :class="['tab-btn', { active: currentTab === 'all' }]" @click="switchTab('all')">全部</button>
<button :class="['tab-btn', { active: currentTab === 'pending' }]" @click="switchTab('pending')">待审核</button>
<button :class="['tab-btn', { active: currentTab === 'pass' }]" @click="switchTab('pass')">已通过</button>
<button :class="['tab-btn', { active: currentTab === 'reject' }]" @click="switchTab('reject')">已拒绝</button>
</div>
<div v-if="loading" class="loading-wrap">
<div class="spinner"></div><div>加载中...</div>
</div>
<div v-else-if="!filteredNews.length" class="empty-state">暂无数据</div>
<div v-else class="table-wrap">
<table>
<thead><tr><th>ID</th><th>标题</th><th>作者</th><th>状态</th><th>风险</th><th>时间</th><th>操作</th></tr></thead>
<tbody>
<tr v-for="n in filteredNews" :key="n.id">
<td>{{ n.id }}</td>
<td><a class="news-title-link" @click="goDetail(n.id)">{{ truncate(n.title, 30) }}</a></td>
<td>{{ n.nickname || '匿名' }}</td>
<td><span :class="['status-badge', n.status==='已通过'?'status-pass':n.status==='待审核'?'status-pending':'status-reject']">{{ n.status }}</span></td>
<td><span v-if="n.risk_level" :class="['status-badge', n.risk_level==='高'?'risk-high':n.risk_level==='中'?'risk-medium':'risk-low']">{{ n.risk_level }}</span><span v-else>-</span></td>
<td>{{ formatTimeShort(n.create_time) }}</td>
<td>
<button class="btn btn-success" @click="reviewNews(n.id, '已通过')">通过</button>
<button class="btn btn-danger" @click="reviewNews(n.id, '已拒绝')">拒绝</button>
<button class="btn btn-secondary" @click="reviewNews(n.id, '待审核')">重置</button>
<button class="btn btn-danger" @click="deleteNews(n.id)">删除</button>
</td>
</tr>
</tbody>
</table>
</div>
</div>
<div class="card">
<div class="card-title"><span>🤖</span> AI辅助记录</div>
<div style="max-height: 500px; overflow-y: auto;">
<div v-if="loadingAI" class="empty-state">加载中...</div>
<div v-else-if="!aiRecords.length" class="empty-state">暂无 AI 辅助记录</div>
<div v-for="item in aiRecords" :key="item.id" class="history-item">
<div class="history-user">用户：{{ item.username || '未知' }}</div>
<div class="history-type">{{ item.assist_type }}</div>
<div class="history-time">{{ formatTimeShort(item.create_time) }}</div>
<div class="history-content"><b>原文：</b>{{ truncate(item.original_content, 40) }}...</div>
<div class="history-content"><b>AI结果：</b>{{ truncate(item.optimized_content, 50) }}...</div>
</div>
</div>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import NavBar from "../components/NavBar.vue";
import { newsApi } from "../api/news";

const router = useRouter();

const currentTab = ref("all");
const allNews = ref<any[]>([]);
const loading = ref(true);
const loadingAI = ref(true);
const aiRecords = ref<any[]>([]);

const statUsers = ref(0);
const statAdmins = ref(0);
const statTotal = ref(0);
const statPass = ref(0);
const statPending = ref(0);
const statReject = ref(0);
const statComments = ref(0);
const statLikes = ref(0);

const filteredNews = computed(() => {
  if (currentTab.value === "pending") return allNews.value.filter(n => n.status === "待审核");
  if (currentTab.value === "pass") return allNews.value.filter(n => n.status === "已通过");
  if (currentTab.value === "reject") return allNews.value.filter(n => n.status === "已拒绝");
  return allNews.value;
});

function truncate(text: string, len: number) {
  if (!text) return "";
  return text.length > len ? text.substring(0, len) + "..." : text;
}

function formatTimeShort(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

function switchTab(tab: string) {
  currentTab.value = tab;
}

function goDetail(id: number) {
  router.push(`/news/${id}`);
}

async function loadNewsAndStats() {
  loading.value = true;
  try {
    const [newsRes, statsRes] = await Promise.all([
      newsApi.adminNews(),
      newsApi.adminUserStats(),
    ]);
    allNews.value = newsRes.data || [];
    const stats = statsRes.data;
    statUsers.value = stats.total_users || 0;
    statAdmins.value = stats.admin_count || 0;
    statTotal.value = allNews.value.length;
    statPass.value = allNews.value.filter(n => n.status === "已通过").length;
    statPending.value = allNews.value.filter(n => n.status === "待审核").length;
    statReject.value = allNews.value.filter(n => n.status === "已拒绝").length;

    let totalLikes = 0, totalComments = 0;
    for (const n of allNews.value) {
      try {
        const s = await newsApi.getStats(n.id);
        totalLikes += s.data.like_count || 0;
        totalComments += s.data.comment_count || 0;
      } catch {}
    }
    statLikes.value = totalLikes;
    statComments.value = totalComments;
  } catch {} finally {
    loading.value = false;
  }
}

async function loadAIHistory() {
  loadingAI.value = true;
  try {
    const res = await newsApi.adminAiRecords();
    aiRecords.value = res.data || [];
  } catch {
    aiRecords.value = [];
  } finally {
    loadingAI.value = false;
  }
}

async function reviewNews(id: number, status: string) {
  if (!confirm(`确定设为：${status}？`)) return;
  try {
    await newsApi.reviewNews(id, status);
    await loadNewsAndStats();
  } catch { alert("操作失败"); }
}

async function deleteNews(id: number) {
  if (!confirm("确定删除？不可恢复！")) return;
  try {
    await newsApi.delete(id);
    await loadNewsAndStats();
  } catch { alert("删除失败"); }
}

onMounted(() => {
  loadNewsAndStats();
  loadAIHistory();
});
</script>

<style scoped>

.admin-toolbar {
  margin-bottom: 20px;
}
.toolbar-link {
  display: inline-block;
  padding: 8px 20px;
  background: linear-gradient(135deg, var(--primary) 0%, #1565c0 100%);
  color: white;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.3s;
}
.toolbar-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.4);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px; margin-bottom: 28px;
}
.stat-card {
  background: var(--surface); border-radius: var(--radius);
  padding: 24px; box-shadow: var(--shadow);
  border: 1px solid var(--border);
  text-align: center; transition: all 0.3s;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.stat-icon { font-size: 32px; margin-bottom: 8px; }
.stat-num { font-size: 32px; font-weight: 800; color: var(--primary); }
.stat-label { font-size: 14px; color: var(--text-muted); margin-top: 4px; }
.main-grid {
  display: grid; grid-template-columns: 2fr 1fr; gap: 24px;
}
.card {
  background: var(--surface); border-radius: var(--radius);
  padding: 24px; box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.card-title {
  font-size: 18px; font-weight: 700;
  margin-bottom: 16px; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px;
  padding-bottom: 12px; border-bottom: 2px solid var(--border);
}
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th {
  background: var(--primary-bg); color: var(--primary-dark);
  padding: 12px; text-align: left;
  font-weight: 700; border-bottom: 2px solid var(--border);
}
td { padding: 12px; border-bottom: 1px solid var(--border); color: var(--text-secondary); }
tr:hover td { background: var(--primary-bg); }
th:nth-child(4), td:nth-child(4) { min-width: 100px; }
th:nth-child(5), td:nth-child(5) { min-width: 90px; }
th:nth-child(7), td:nth-child(7) { white-space: nowrap; }
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
.btn {
  padding: 6px 14px; border: none; border-radius: 8px;
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all 0.3s; margin-right: 4px;
}
.btn-success { background: #e8f5e9; color: #2e7d32; }
.btn-success:hover { background: #c8e6c9; }
.btn-danger { background: #ffebee; color: #c62828; }
.btn-danger:hover { background: #ffcdd2; }
.btn-secondary { background: var(--primary-bg); color: var(--primary-dark); }
.btn-secondary:hover { background: #bbdefb; }
.news-title-link {
  color: var(--primary-dark);
  font-weight: 600; text-decoration: none; cursor: pointer;
}
.news-title-link:hover { text-decoration: underline; }
.history-item {
  background: var(--primary-bg); border-radius: var(--radius-sm);
  padding: 12px; margin-bottom: 10px;
  border-left: 4px solid var(--primary-light);
}
.history-type { font-size: 12px; color: var(--primary-dark); font-weight: 700; margin-bottom: 4px; }
.history-time { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
.history-content { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.history-user { font-size: 11px; color: var(--primary); font-weight: 600; margin-bottom: 4px; }
.empty-state {
  text-align: center; padding: 40px 20px;
  color: var(--text-muted); font-size: 14px;
}
.tab-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.tab-btn {
  padding: 8px 16px; border: 2px solid var(--border);
  border-radius: var(--radius-sm); background: white;
  cursor: pointer; font-size: 14px;
  font-weight: 600; color: var(--text-secondary);
  transition: all 0.3s;
}
.tab-btn.active {
  border-color: var(--primary); background: var(--primary);
  color: white;
}
.tab-btn:hover:not(.active) { border-color: var(--primary-light); color: var(--primary); }
.loading-wrap { text-align: center; padding: 40px; color: var(--primary); }
.spinner {
  display: inline-block; width: 32px; height: 32px;
  border: 3px solid rgba(33,150,243,0.15); border-radius: 50%;
  border-top-color: var(--primary); animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .stats-grid { grid-template-columns: 1fr; }
  th, td { padding: 8px; font-size: 12px; }
}
</style>
