<template>
<div class="page-container">
<NavBar />

<div class="hero">
<h1>🛡️ 智能风控新闻发布平台</h1>
<p>AI创作辅助 × 智能风控审核 × 安全内容生态<br>每一条新闻都经过AI严格审核，确保内容合法合规</p>
<div class="hero-stats">
<div class="hero-stat">
<div class="hero-stat-num">{{ stats.passCount }}</div>
<div class="hero-stat-label">已通过新闻</div>
</div>
<div class="hero-stat">
<div class="hero-stat-num">{{ stats.commentCount }}</div>
<div class="hero-stat-label">用户评论</div>
</div>
<div class="hero-stat">
<div class="hero-stat-num">{{ stats.likeCount }}</div>
<div class="hero-stat-label">累计点赞</div>
</div>
</div>
</div>

<div class="section-title"><span>📰</span> 最新新闻</div>
<div id="newsContainer">
<div v-if="loading" class="loading-wrap">
<div class="spinner"></div>
<div>正在加载新闻...</div>
</div>
<div v-else-if="!newsList.length" class="empty-state">
<div class="empty-icon">📭</div>
<h3>暂无新闻</h3>
<p>还没有通过审核的新闻，去创作一篇吧！</p>
<br><router-link to="/news/create" style="padding:10px 20px;background:var(--primary);color:white;border-radius:12px;text-decoration:none;">去创作 →</router-link>
</div>
<div v-else class="news-grid">
<div v-for="n in newsList" :key="n.id" class="news-card" :id="'card-' + n.id">
<div class="news-card-title" @click="goDetail(n.id)">{{ n.title }}</div>
<div class="news-card-content" @click="goDetail(n.id)" v-html="n.content"></div>
<div class="news-card-meta">
<span class="news-source-tag">{{ n.source || '官方发布' }}</span>
<span>{{ formatTime(n.create_time) }}</span>
</div>
<div class="news-actions">
<button :class="['action-btn', { active: getStats(n.id).is_liked }]" @click.stop="toggleLike(n.id)">
<span>{{ getStats(n.id).is_liked ? '❤️' : '🤍' }}</span>
<span class="count">{{ getStats(n.id).like_count }}</span>
</button>
<button :class="['action-btn', { active: getStats(n.id).is_favorited }]" @click.stop="toggleFavorite(n.id)">
<span>{{ getStats(n.id).is_favorited ? '⭐' : '☆' }}</span>
<span class="count">{{ getStats(n.id).favorite_count }}</span>
</button>
<button class="action-btn" @click.stop="toggleComment(n.id)">
<span>💬</span>
<span class="count">{{ getStats(n.id).comment_count }}</span>
</button>
</div>
<div :class="['comment-section', { show: commentOpen === n.id }]">
<div class="comment-input-wrap">
<input type="text" class="comment-input" v-model="commentInputs[n.id]" placeholder="发表您的评论..." maxlength="200" @keypress.enter="postComment(n.id)">
<button class="comment-btn" @click.stop="postComment(n.id)">发送</button>
</div>
<div class="comment-list">
<div v-if="!comments[n.id] || !comments[n.id].length" style="color:var(--text-muted);font-size:12px;text-align:center;padding:8px;">暂无评论，快来抢沙发！</div>
<div v-for="c in comments[n.id]" :key="c.id || c.create_time" class="comment-item">
<span class="comment-author">{{ c.nickname }}</span>
<span class="comment-time">{{ formatTime(c.create_time) }}</span>
<div class="comment-text">{{ c.content }}</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { newsApi } from "../api/news";
import NavBar from "../components/NavBar.vue";

const router = useRouter();

const loading = ref(true);
const newsList = ref<any[]>([]);
const newsStats = reactive<Record<number, any>>({});
const comments = reactive<Record<number, any[]>>({});
const commentInputs = reactive<Record<number, string>>({});
const commentOpen = ref<number | null>(null);

const defaults = { like_count: 0, favorite_count: 0, comment_count: 0, is_liked: false, is_favorited: false };

const stats = reactive({ passCount: 0, commentCount: 0, likeCount: 0 });

function getStats(newsId: number) {
  return newsStats[newsId] || defaults;
}

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

async function loadHeroStats() {
  try {
    const res = await newsApi.list();
    const allNews: any[] = res.data || [];
    const passCount = allNews.filter((n: any) => n.status === "已通过").length;
    let totalComments = 0, totalLikes = 0;
    for (const n of allNews) {
      try {
        const s = await newsApi.getStats(n.id);
        totalLikes += s.data.like_count || 0;
        totalComments += s.data.comment_count || 0;
      } catch {}
    }
    stats.passCount = passCount;
    stats.commentCount = totalComments;
    stats.likeCount = totalLikes;
  } catch {}
}

async function loadNews() {
  loading.value = true;
  try {
    const res = await newsApi.list();
    const news: any[] = res.data || [];
    newsList.value = news;
    for (const n of news) {
      try {
        const s = await newsApi.getStats(n.id);
        newsStats[n.id] = s.data;
      } catch {
        newsStats[n.id] = { ...defaults };
      }
    }
  } catch {
    newsList.value = [];
  } finally {
    loading.value = false;
  }
}

async function toggleLike(newsId: number) {
  try {
    const res = await newsApi.toggleLike(newsId);
    const data = res.data;
    newsStats[newsId] = { ...newsStats[newsId], is_liked: data.liked };
    const s = await newsApi.getStats(newsId);
    newsStats[newsId] = { ...newsStats[newsId], ...s.data };
  } catch (err: any) {
    alert("操作失败：" + (err.response?.data?.detail || err.message));
  }
}

async function toggleFavorite(newsId: number) {
  try {
    const res = await newsApi.toggleFavorite(newsId);
    const data = res.data;
    newsStats[newsId] = { ...newsStats[newsId], is_favorited: data.favorited };
    const s = await newsApi.getStats(newsId);
    newsStats[newsId] = { ...newsStats[newsId], ...s.data };
  } catch (err: any) {
    alert("操作失败：" + (err.response?.data?.detail || err.message));
  }
}

async function toggleComment(newsId: number) {
  if (commentOpen.value === newsId) {
    commentOpen.value = null;
  } else {
    commentOpen.value = newsId;
    await loadComments(newsId);
  }
}

async function loadComments(newsId: number) {
  try {
    const res = await newsApi.getComments(newsId);
    comments[newsId] = res.data || [];
  } catch {
    comments[newsId] = [];
  }
}

async function postComment(newsId: number) {
  const content = (commentInputs[newsId] || "").trim();
  if (!content) { alert("请输入评论内容"); return; }
  try {
    await newsApi.postComment(newsId, content);
    commentInputs[newsId] = "";
    await loadComments(newsId);
    const s = await newsApi.getStats(newsId);
    newsStats[newsId] = { ...newsStats[newsId], ...s.data };
  } catch (err: any) {
    alert("评论失败：" + (err.response?.data?.detail || err.message));
  }
}

function goDetail(id: number) {
  router.push(`/news/${id}`);
}

onMounted(() => {
  loadNews();
  loadHeroStats();
});
</script>

<style scoped>

.hero {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  padding: 48px 40px;
  margin-bottom: 32px;
  color: white;
  text-align: center;
  box-shadow: var(--shadow-hover);
}
.hero h1 { font-size: 32px; font-weight: 800; margin-bottom: 12px; }
.hero p { font-size: 16px; opacity: 0.9; max-width: 600px; margin: 0 auto; }
.hero-stats {
  display: flex; justify-content: center; gap: 40px; margin-top: 24px;
}
.hero-stat { text-align: center; }
.hero-stat-num { font-size: 28px; font-weight: 800; }
.hero-stat-label { font-size: 13px; opacity: 0.85; margin-top: 4px; }
.section-title {
  font-size: 20px; font-weight: 700;
  margin-bottom: 20px; display: flex;
  align-items: center; gap: 10px; color: var(--text-primary);
}
.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}
.news-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: all 0.35s ease;
  cursor: pointer;
  display: flex; flex-direction: column;
}
.news-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-hover);
  border-color: var(--primary-light);
}
.news-card-title {
  font-size: 18px; font-weight: 700;
  color: var(--text-primary); margin-bottom: 10px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.news-card-content {
  font-size: 14px; color: var(--text-secondary);
  line-height: 1.8; margin-bottom: 16px; flex: 1;
  max-height: 5.6em;
  overflow: hidden;
}
.news-card-meta {
  display: flex; justify-content: space-between;
  align-items: center; font-size: 13px; color: var(--text-muted);
  margin-bottom: 14px;
}
.news-source-tag {
  background: var(--primary-bg); color: var(--primary-dark);
  padding: 3px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.news-actions {
  display: flex; gap: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}
.action-btn {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 6px; padding: 8px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: white;
  color: var(--text-secondary); font-size: 13px;
  font-weight: 600; cursor: pointer; transition: all 0.3s;
}
.action-btn:hover { background: var(--primary-bg); border-color: var(--primary-light); color: var(--primary-dark); }
.action-btn.active {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; border-color: var(--primary);
}
.action-btn .count { font-weight: 700; }
.comment-section {
  margin-top: 16px; padding-top: 16px;
  border-top: 1px dashed var(--border);
  display: none;
}
.comment-section.show { display: block; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.comment-input-wrap { display: flex; gap: 8px; margin-bottom: 12px; }
.comment-input {
  flex: 1; padding: 8px 12px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-family: inherit; outline: none;
}
.comment-input:focus { border-color: var(--primary-light); box-shadow: 0 0 0 3px rgba(33,150,243,0.1); }
.comment-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; border: none; border-radius: var(--radius-sm);
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.3s;
}
.comment-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(33,150,243,0.3); }
.comment-list { max-height: 160px; overflow-y: auto; }
.comment-item {
  padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px;
}
.comment-item:last-child { border-bottom: none; }
.comment-author { font-weight: 700; color: var(--primary-dark); margin-right: 6px; }
.comment-time { color: var(--text-muted); font-size: 11px; }
.comment-text { color: var(--text-secondary); margin-top: 2px; line-height: 1.5; }
.empty-state {
  text-align: center; padding: 80px 20px; color: var(--text-muted);
}
.empty-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.4; }
.loading-wrap { text-align: center; padding: 60px; color: var(--primary); }
.spinner {
  display: inline-block; width: 36px; height: 36px;
  border: 3px solid rgba(33,150,243,0.15); border-radius: 50%;
  border-top-color: var(--primary); animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) {
  .news-grid { grid-template-columns: 1fr; }
  .hero h1 { font-size: 24px; }
  .hero-stats { gap: 20px; }
}
</style>
