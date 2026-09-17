<template>
<div class="detail-wrapper">
<div class="page-container">
<NavBar />

<div class="card" id="detailCard">
<div v-if="loading" class="loading">
<div class="spinner"></div>
<div>正在加载新闻详情...</div>
</div>
<div v-else-if="errorMsg" class="error-state">
<h2>😕 {{ errorMsg }}</h2>
<br><router-link to="/" class="btn btn-primary">返回首页</router-link>
</div>
<template v-else>
<div class="news-header">
<h1 class="news-title">{{ news.title }}</h1>
<div class="news-meta-bar">
<div class="meta-item">
<span>📰</span>
<span :class="['status-badge', news.status==='已通过'?'status-pass':news.status==='待审核'?'status-pending':'status-reject']">{{ news.status }}</span>
</div>
<div class="meta-item"><span>👤</span><span>{{ news.nickname || '匿名' }}</span></div>
<div class="meta-item"><span>🏢</span><span>{{ news.source || '未知来源' }}</span></div>
<div class="meta-item"><span>🕐</span><span>{{ formatTime(news.create_time) }}</span></div>
<div v-if="news.risk_level" class="meta-item">
<span>🛡️</span>
<span :class="['status-badge', news.risk_level==='高'?'risk-high':news.risk_level==='中'?'risk-medium':'risk-low']">{{ news.risk_level }}风险</span>
</div>
</div>
</div>

<div class="news-content" v-html="news.content"></div>

<div v-if="news.risk_reason" class="risk-panel">
<div class="risk-panel-title">⚠️ 风控审核结果</div>
<div class="risk-panel-text">
<strong>审核状态：</strong>{{ news.status }}<br>
<strong>风险等级：</strong><span :class="['status-badge', news.risk_level==='高'?'risk-high':news.risk_level==='中'?'risk-medium':'risk-low']">{{ news.risk_level }}</span><br>
<strong>违规原因：</strong>{{ news.risk_reason }}
</div>
</div>

<div class="news-actions-bar">
<button :class="['action-big', { active: stats.is_liked }]" @click="toggleLike">
<span>{{ stats.is_liked ? '❤️' : '🤍' }}</span>
<span class="count">{{ stats.like_count }}</span>
<span>点赞</span>
</button>
<button :class="['action-big', { active: stats.is_favorited }]" @click="toggleFavorite">
<span>{{ stats.is_favorited ? '⭐' : '☆' }}</span>
<span class="count">{{ stats.favorite_count }}</span>
<span>收藏</span>
</button>
<button class="action-big">
<span>💬</span>
<span class="count">{{ stats.comment_count }}</span>
<span>评论</span>
</button>
</div>

<div class="comment-section">
<div class="comment-section-title"><span>💬</span> 评论区</div>
<div class="comment-input-wrap">
<input type="text" class="comment-input" v-model="commentInput" placeholder="发表您的评论..." maxlength="300">
<button class="comment-btn" @click="postComment">发表评论</button>
</div>
<div class="comment-list">
<div v-if="!comments.length" class="empty-comments">暂无评论，快来抢沙发！</div>
<div v-for="c in comments" :key="c.id || c.create_time" class="comment-item">
<div class="comment-item-header">
<span class="comment-author">{{ c.nickname }}</span>
<span class="comment-time">{{ formatTime(c.create_time) }}</span>
</div>
<div class="comment-text">{{ c.content }}</div>
</div>
</div>
</div>

<div v-if="userStore.isAdmin" class="admin-actions">
<span style="font-weight:700; color:#1a237e; margin-right:8px;">管理员操作：</span>
<button class="btn btn-success" @click="adminReview('已通过')">✅ 通过审核</button>
<button class="btn btn-danger" @click="adminReview('已拒绝')">❌ 拒绝审核</button>
<button class="btn btn-secondary" @click="adminReview('待审核')">⏳ 重置待审</button>
<button class="btn btn-danger" @click="deleteNews">🗑️ 删除新闻</button>
</div>
</template>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "../stores/user";
import NavBar from "../components/NavBar.vue";
import { newsApi } from "../api/news";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const loading = ref(true);
const errorMsg = ref("");
const news = ref<any>({});
const stats = ref<any>({ like_count: 0, favorite_count: 0, comment_count: 0, is_liked: false, is_favorited: false });
const comments = ref<any[]>([]);
const commentInput = ref("");

const newsId = computed(() => Number(route.params.id));

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

async function loadDetail() {
  loading.value = true;
  const id = newsId.value;
  if (!id) {
    errorMsg.value = "缺少新闻ID参数";
    loading.value = false;
    return;
  }
  try {
    const [newsRes, statsRes, commentsRes] = await Promise.all([
      newsApi.detail(id),
      newsApi.getStats(id),
      newsApi.getComments(id),
    ]);
    news.value = newsRes.data;
    stats.value = statsRes.data;
    comments.value = commentsRes.data || [];
  } catch (err: any) {
    errorMsg.value = "加载失败：" + (err.response?.data?.detail || err.message);
  } finally {
    loading.value = false;
  }
}

async function toggleLike() {
  const id = newsId.value;
  try {
    const res = await newsApi.toggleLike(id);
    stats.value = { ...stats.value, is_liked: res.data.liked };
    const s = await newsApi.getStats(id);
    stats.value = { ...stats.value, ...s.data };
  } catch (err: any) {
    alert("操作失败：" + (err.response?.data?.detail || err.message));
  }
}

async function toggleFavorite() {
  const id = newsId.value;
  try {
    const res = await newsApi.toggleFavorite(id);
    stats.value = { ...stats.value, is_favorited: res.data.favorited };
    const s = await newsApi.getStats(id);
    stats.value = { ...stats.value, ...s.data };
  } catch (err: any) {
    alert("操作失败：" + (err.response?.data?.detail || err.message));
  }
}

async function postComment() {
  const content = commentInput.value.trim();
  if (!content) { alert("请输入评论内容"); return; }
  try {
    await newsApi.postComment(newsId.value, content);
    commentInput.value = "";
    await loadDetail();
  } catch (err: any) {
    alert("评论失败：" + (err.response?.data?.detail || err.message));
  }
}

async function adminReview(status: string) {
  if (!confirm(`确定将新闻状态修改为「${status}」吗？`)) return;
  try {
    await newsApi.reviewNews(newsId.value, status);
    alert(`审核状态已更新为「${status}」`);
    await loadDetail();
  } catch (err: any) {
    alert("操作失败：" + (err.response?.data?.detail || err.message));
  }
}

async function deleteNews() {
  if (!confirm("确定删除这条新闻吗？此操作不可恢复！")) return;
  try {
    await newsApi.delete(newsId.value);
    alert("删除成功");
    router.push("/news/my");
  } catch (err: any) {
    alert("删除失败：" + (err.response?.data?.detail || err.message));
  }
}

onMounted(() => {
  loadDetail();
});
</script>

<style scoped>
.detail-wrapper {
  background: linear-gradient(180deg, #e8f4fd 100%);
  min-height: 100vh;
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.news-header {
  border-bottom: 2px solid var(--border);
  padding-bottom: 24px;
  margin-bottom: 28px;
}
.news-title {
  font-size: 30px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 18px;
}
.news-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  font-size: 14px;
  color: var(--text-secondary);
}
.meta-item { display: flex; align-items: center; gap: 6px; }
.status-badge {
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}
.status-pass { background: #e8f5e9; color: #2e7d32; }
.status-pending { background: #fff8e1; color: #f57f17; }
.status-reject { background: #ffebee; color: #c62828; }
.risk-high { background: #ef5350; color: white; }
.risk-medium { background: #ffca28; color: #5d4037; }
.risk-low { background: #66bb6a; color: white; }
.news-content {
  font-size: 17px;
  line-height: 1.9;
  color: var(--text-secondary);
}
.news-content p { margin-bottom: 1.2em; }
.news-content h1, .news-content h2, .news-content h3 {
  margin: 1em 0 0.6em 0;
  font-weight: 700;
  color: var(--text-primary);
}
.news-content strong { color: var(--text-primary); }
.news-actions-bar {
  display: flex; gap: 12px; margin-top: 28px;
  padding-top: 20px; border-top: 2px solid var(--border);
}
.action-big {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  gap: 8px; padding: 14px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  background: white; color: var(--text-secondary);
  font-size: 15px; font-weight: 700;
  cursor: pointer; transition: all 0.3s;
}
.action-big:hover { background: var(--primary-bg); border-color: var(--primary-light); color: var(--primary-dark); }
.action-big.active {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(33,150,243,0.3);
}
.action-big .count { font-size: 18px; }
.comment-section {
  margin-top: 24px; padding-top: 24px;
  border-top: 2px solid var(--border);
}
.comment-section-title {
  font-size: 18px; font-weight: 700;
  margin-bottom: 16px; color: var(--text-primary);
  display: flex; align-items: center; gap: 8px;
}
.comment-input-wrap { display: flex; gap: 10px; margin-bottom: 20px; }
.comment-input {
  flex: 1; padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px; font-family: inherit; outline: none;
}
.comment-input:focus { border-color: var(--primary-light); box-shadow: 0 0 0 4px rgba(33,150,243,0.1); }
.comment-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; border: none;
  border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.3s;
}
.comment-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(33,150,243,0.3); }
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-item {
  background: var(--primary-bg);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  border: 1px solid var(--border);
}
.comment-item-header {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 6px;
}
.comment-author { font-weight: 700; color: var(--primary-dark); font-size: 14px; }
.comment-time { color: var(--text-muted); font-size: 12px; }
.comment-text { color: var(--text-secondary); font-size: 14px; line-height: 1.6; }
.empty-comments {
  text-align: center; padding: 40px; color: var(--text-muted);
}
.risk-panel {
  background: #ffebee;
  border: 1px solid #ef9a9a;
  border-radius: var(--radius-sm);
  padding: 20px; margin-top: 24px;
}
.risk-panel-title {
  font-size: 16px; font-weight: 700;
  color: #c62828; margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.risk-panel-text { font-size: 14px; color: #b71c1c; line-height: 1.6; }
.admin-actions {
  margin-top: 24px; padding-top: 20px;
  border-top: 2px solid var(--border);
  display: flex; gap: 12px; flex-wrap: wrap;
}
.btn {
  padding: 10px 20px; border: none;
  border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.3s;
}
.btn-primary {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(33,150,243,0.4); }
.btn-success { background: #e8f5e9; color: #2e7d32; }
.btn-success:hover { background: #c8e6c9; }
.btn-danger { background: #ffebee; color: #c62828; }
.btn-danger:hover { background: #ffcdd2; }
.btn-secondary { background: var(--primary-bg); color: var(--primary-dark); }
.btn-secondary:hover { background: #bbdefb; }
.loading { text-align: center; padding: 60px; color: var(--primary); }
.spinner {
  display: inline-block; width: 40px; height: 40px;
  border: 3px solid rgba(33,150,243,0.15);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-state { text-align: center; padding: 60px 20px; color: #c62828; }
@media (max-width: 600px) {
  .news-title { font-size: 22px; }
  .card { padding: 20px; }
  .news-actions-bar { flex-wrap: wrap; }
  .action-big { flex: 1 1 45%; }
}
</style>
