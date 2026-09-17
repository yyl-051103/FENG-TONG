<template>
<div class="profile-wrapper">
<div class="page-container">
<NavBar />

<div class="profile-header">
<div class="avatar">{{ profileAvatar }}</div>
<div class="profile-info">
<h1>{{ profileName }}</h1>
<p>账号：{{ profileAccount }}</p>
<p>手机号：{{ profilePhone || '未绑定' }} 
  <button class="btn-edit-phone" @click="showPhoneModal = true">
    {{ profilePhone ? '修改' : '绑定' }}
  </button>
</p>
<span class="profile-role">{{ profileRole }}</span>
</div>
</div>

<div class="score-section">
  <div class="score-card">
    <div class="score-left">
      <div class="score-label">我的积分</div>
      <div class="score-num">{{ scoreBalance }}</div>
    </div>
    <button class="score-detail-btn" @click="goScore">查看积分明细 →</button>
  </div>
  <div class="score-recent" v-if="recentRecords.length">
    <div class="score-recent-title">最近积分记录</div>
    <div v-for="r in recentRecords" :key="r.id" class="score-item">
      <span class="score-item-desc">{{ r.description }}</span>
      <span :class="['score-item-val', r.type === 'earn' ? 'earn' : 'consume']">
        {{ r.type === 'earn' ? '+' : '' }}{{ r.score }}
      </span>
      <span class="score-item-time">{{ formatTime(r.create_time) }}</span>
    </div>
  </div>
</div>

<div class="stats-row">
<div class="stat-card"><div class="stat-num">{{ statTotal }}</div><div class="stat-label">总发布数</div></div>
<div class="stat-card"><div class="stat-num">{{ statPass }}</div><div class="stat-label">已通过</div></div>
<div class="stat-card"><div class="stat-num">{{ statAI }}</div><div class="stat-label">AI辅助次数</div></div>
<div class="stat-card stat-card-clickable" @click="goFavorites"><div class="stat-num">{{ statFav }}</div><div class="stat-label">我的收藏</div></div>
</div>

<div class="main-grid">
<div class="card">
<div class="card-title"><span>📋</span> 我的发布记录</div>
<div style="max-height: 400px; overflow-y: auto;">
<div v-if="!myNews.length" class="empty-state">暂无发布记录</div>
<div v-for="n in myNews" :key="n.id" class="news-item">
<router-link :to="'/news/' + n.id" class="news-item-title">{{ n.title }}</router-link>
<div class="news-item-meta">
<span :class="['status-badge', n.status==='已通过'?'status-pass':n.status==='待审核'?'status-pending':'status-reject']">{{ n.status }}</span>
<span>{{ formatTime(n.create_time) }}</span>
</div>
<div v-if="n.risk_reason" style="font-size:12px; color:#c62828; margin-top:4px;">{{ n.risk_reason }}</div>
<div style="margin-top:8px; display:flex; gap:6px;">
<button class="btn btn-secondary" @click="viewDetail(n.id)">查看</button>
<button class="btn btn-danger" @click="deleteNews(n.id)">删除</button>
</div>
</div>
</div>
</div>
<div class="card">
<div class="card-title"><span>⭐</span> 我的收藏</div>
<div style="max-height: 400px; overflow-y: auto;">
<div v-if="!myFavorites.length" class="empty-state">暂无收藏的新闻</div>
<div v-for="item in myFavorites" :key="(item.news || item).id || item.id" class="news-item">
<router-link :to="'/news/' + ((item.news || item).id)" class="news-item-title">{{ (item.news || item).title || '无标题' }}</router-link>
<div class="news-item-meta">
<span>收藏内容</span>
<span>{{ formatTime((item.news || item).create_time || item.create_time) }}</span>
</div>
</div>
</div>
</div>
</div>

<div class="card" style="margin-top: 24px;">
<div class="card-title"><span>🤖</span> AI创作辅助历史</div>
<div style="max-height: 300px; overflow-y: auto;">
<div v-if="!aiHistory.length" class="empty-state">暂无AI辅助记录</div>
<div v-for="r in aiHistory" :key="r.id" class="history-item">
<div class="history-type">{{ r.assist_type || 'AI辅助' }}</div>
<div class="history-time">{{ formatTime(r.create_time) }}</div>
<div class="history-content">{{ truncate(r.optimized_content, 100) }}...</div>
<div class="history-actions">
<button class="btn btn-danger" @click="deleteRecord(r.id)">删除</button>
</div>
</div>
</div>
</div>

<div v-if="showPhoneModal" class="modal-overlay" @click.self="showPhoneModal = false">
  <div class="modal-card">
    <h3>{{ profilePhone ? '修改手机号' : '绑定手机号' }}</h3>
    <div class="form-group">
      <label class="form-label">新手机号</label>
      <input type="tel" class="form-input" v-model="newPhone" placeholder="请输入新手机号" maxlength="11">
    </div>
    <div class="form-group sms-row">
      <input type="text" class="form-input sms-input" v-model="newSmsCode" placeholder="验证码" maxlength="6">
      <button type="button" class="btn-sms" @click="sendChangeSms" :disabled="changeSmsCountdown > 0">
        {{ changeSmsCountdown > 0 ? changeSmsCountdown + 's后重发' : '获取验证码' }}
      </button>
    </div>
    <div class="modal-actions">
      <button class="btn btn-cancel" @click="showPhoneModal = false">取消</button>
      <button class="btn btn-confirm" @click="confirmChangePhone">确认</button>
    </div>
  </div>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";
import { authApi } from "../api/auth";
import { newsApi } from "../api/news";
import request from "../api/request";
import NavBar from "../components/NavBar.vue";

const router = useRouter();
const userStore = useUserStore();

const profileName = computed(() => userStore.userInfo?.nickname || userStore.userInfo?.username || userStore.userInfo?.phone || "用户");
const profileAccount = computed(() => userStore.userInfo?.username || "");
const profilePhone = computed(() => userStore.userInfo?.phone || "");
const profileRole = computed(() => userStore.isAdmin ? "🔧 管理员" : "👤 普通用户");
const profileAvatar = computed(() => userStore.isAdmin ? "🔧" : "👤");

const statTotal = ref(0);
const statPass = ref(0);
const statAI = ref(0);
const statFav = ref(0);
const myNews = ref<any[]>([]);
const myFavorites = ref<any[]>([]);
const aiHistory = ref<any[]>([]);

const scoreBalance = ref(0);
const recentRecords = ref<any[]>([]);

const showPhoneModal = ref(false);
const newPhone = ref("");
const newSmsCode = ref("");
const changeSmsCountdown = ref(0);
let changeSmsTimer: ReturnType<typeof setInterval> | null = null;

async function sendChangeSms() {
  const p = newPhone.value.trim();
  if (!p || p.length !== 11) { alert("请输入正确的手机号"); return; }
  try {
    await authApi.sendSms({ phone: p });
    alert("验证码已发送");
    changeSmsCountdown.value = 60;
    changeSmsTimer = setInterval(() => {
      changeSmsCountdown.value--;
      if (changeSmsCountdown.value <= 0 && changeSmsTimer) { clearInterval(changeSmsTimer); changeSmsTimer = null; }
    }, 1000);
  } catch (err: any) {
    alert("发送失败：" + (err.response?.data?.detail || err.message));
  }
}

async function confirmChangePhone() {
  const p = newPhone.value.trim();
  const c = newSmsCode.value.trim();
  if (!p || p.length !== 11) { alert("请输入正确的手机号"); return; }
  if (!c) { alert("请输入验证码"); return; }
  try {
    const res = await authApi.changePhone({ phone: p, sms_code: c });
    alert(res.data.msg || "修改成功");
    if (userStore.userInfo) userStore.userInfo.phone = p;
    userStore.persist?.();
    showPhoneModal.value = false;
    newPhone.value = "";
    newSmsCode.value = "";
  } catch (err: any) {
    alert("修改失败：" + (err.response?.data?.detail || err.message));
  }
}

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

function truncate(text: string, len: number) {
  return text ? text.substring(0, len) : "";
}

function viewDetail(id: number) {
  router.push(`/news/${id}`);
}

async function loadMyNews() {
  try {
    const res = await newsApi.my();
    const news: any[] = res.data || [];
    let pass = 0;
    news.forEach((n: any) => { if (n.status === "已通过") pass++; });
    statTotal.value = news.length;
    statPass.value = pass;
    myNews.value = news;
  } catch {
    myNews.value = [];
  }
}

async function loadMyFavorites() {
  try {
    const res = await newsApi.getFavorites();
    const favs: any[] = res.data || [];
    statFav.value = favs.length;
    myFavorites.value = favs;
  } catch {
    myFavorites.value = [];
  }
}

async function loadAIHistory() {
  try {
    const res = await newsApi.aiRecords();
    const records: any[] = res.data || [];
    statAI.value = records.length;
    aiHistory.value = records;
  } catch {
    aiHistory.value = [];
  }
}

async function deleteNews(id: number) {
  if (!confirm("确定删除这条新闻吗？")) return;
  try {
    await newsApi.delete(id);
    await loadMyNews();
  } catch { alert("删除失败"); }
}

async function deleteRecord(id: number) {
  if (!confirm("确定删除这条记录吗？")) return;
  try {
    await newsApi.deleteAiRecord(id);
    await loadAIHistory();
  } catch { alert("删除失败"); }
}

async function loadScoreData() {
  try {
    const res = await request.get("/api/score/balance");
    scoreBalance.value = res.data.data?.balance ?? 0;
  } catch {
    scoreBalance.value = 0;
  }
  try {
    const res = await request.get("/api/score/records", { params: { page_size: 5 } });
    recentRecords.value = res.data.data?.items || [];
  } catch {
    recentRecords.value = [];
  }
}

function goScore() {
  router.push("/score");
}

function goFavorites() {
  router.push("/favorites");
}

onMounted(() => {
  userStore.fetchUserInfo();
  loadMyNews();
  loadMyFavorites();
  loadAIHistory();
  loadScoreData();
});
</script>

<style scoped>
.profile-wrapper {
  background: linear-gradient(180deg, #e8f4fd 100%);
  min-height: 100vh;
}

.profile-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  padding: 40px; margin-bottom: 28px;
  color: white; display: flex;
  align-items: center; gap: 24px;
  box-shadow: var(--shadow-hover);
}
.avatar {
  width: 80px; height: 80px; border-radius: 50%;
  background: rgba(255,255,255,0.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; border: 3px solid rgba(255,255,255,0.4);
}
.profile-info h1 { font-size: 26px; font-weight: 800; margin-bottom: 6px; }
.profile-info p { opacity: 0.9; font-size: 15px; }
.profile-role {
  display: inline-block;
  padding: 4px 14px; border-radius: 20px;
  background: rgba(255,255,255,0.25);
  font-size: 13px; font-weight: 700; margin-top: 8px;
}
.btn-edit-phone {
  background: none; border: 1px solid rgba(255,255,255,0.4); color: white;
  padding: 2px 10px; border-radius: 12px; font-size: 12px; cursor: pointer;
  margin-left: 8px; transition: all 0.3s;
}
.btn-edit-phone:hover { background: rgba(255,255,255,0.2); }
.score-section {
  margin-bottom: 24px;
}
.score-card {
  background: linear-gradient(135deg, #f57f17 0%, #ff8f00 100%);
  border-radius: var(--radius);
  padding: 24px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  box-shadow: var(--shadow);
}
.score-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.score-label {
  font-size: 13px;
  opacity: 0.85;
}
.score-num {
  font-size: 36px;
  font-weight: 800;
}
.score-detail-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-sm);
  color: white;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.score-detail-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}
.score-recent {
  margin-top: 12px;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 16px 20px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.score-recent-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}
.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.score-item:last-child {
  border-bottom: none;
}
.score-item-desc {
  flex: 1;
  color: var(--text-primary);
  font-weight: 600;
}
.score-item-val {
  font-weight: 800;
  white-space: nowrap;
}
.score-item-val.earn {
  color: #2e7d32;
}
.score-item-val.consume {
  color: #c62828;
}
.score-item-time {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}
.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 16px; margin-bottom: 24px;
}
.stat-card {
  background: var(--surface);
  border-radius: var(--radius-sm);
  padding: 20px; text-align: center;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.stat-card-clickable {
  cursor: pointer;
  transition: all 0.3s;
}
.stat-card-clickable:hover {
  background: var(--primary-bg);
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.stat-num { font-size: 28px; font-weight: 800; color: var(--primary); }
.stat-label { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
.main-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
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
.news-item {
  padding: 12px; border-bottom: 1px solid var(--border);
  transition: all 0.2s; border-radius: var(--radius-sm);
}
.news-item:hover { background: var(--primary-bg); }
.news-item:last-child { border-bottom: none; }
.news-item-title {
  font-weight: 600; color: var(--primary-dark);
  font-size: 14px; margin-bottom: 4px;
  cursor: pointer; text-decoration: none;
}
.news-item-title:hover { text-decoration: underline; }
.news-item-meta {
  font-size: 12px; color: var(--text-muted);
  display: flex; justify-content: space-between; align-items: center;
}
.status-badge {
  padding: 2px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 700;
}
.status-pass { background: #e8f5e9; color: #2e7d32; }
.status-pending { background: #fff8e1; color: #f57f17; }
.status-reject { background: #ffebee; color: #c62828; }
.btn {
  padding: 6px 14px; border: none; border-radius: 8px;
  font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.3s;
}
.btn-danger { background: #ffebee; color: #c62828; }
.btn-danger:hover { background: #ffcdd2; }
.btn-secondary { background: var(--primary-bg); color: var(--primary-dark); }
.btn-secondary:hover { background: #bbdefb; }
.history-item {
  background: var(--primary-bg); border-radius: var(--radius-sm);
  padding: 12px; margin-bottom: 10px;
  border-left: 4px solid var(--primary-light);
}
.history-type { font-size: 12px; color: var(--primary-dark); font-weight: 700; margin-bottom: 4px; }
.history-time { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
.history-content { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.history-actions { display: flex; gap: 6px; margin-top: 8px; }
.empty-state {
  text-align: center; padding: 40px 20px;
  color: var(--text-muted); font-size: 14px;
}
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  background: white; border-radius: 12px; padding: 32px; width: 400px; max-width: 90vw;
}
.modal-card h3 { margin-bottom: 20px; font-size: 18px; }
.modal-actions { display: flex; gap: 12px; margin-top: 20px; justify-content: flex-end; }
.btn-cancel { padding: 10px 20px; background: #eee; border: none; border-radius: 8px; cursor: pointer; }
.btn-confirm { padding: 10px 20px; background: var(--primary); color: white; border: none; border-radius: 8px; cursor: pointer; }
.sms-row { display: flex; gap: 10px; align-items: center; }
.sms-input { flex: 1; }
.btn-sms {
  white-space: nowrap; padding: 12px 16px;
  background: var(--primary-bg); color: var(--primary-dark);
  border: 2px solid var(--primary-light); border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s;
}
.btn-sms:hover:not(:disabled) { background: #bbdefb; }
.btn-sms:disabled { opacity: 0.5; cursor: not-allowed; }
@media (max-width: 900px) {
  .main-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .profile-header { flex-direction: column; text-align: center; }
}
</style>
