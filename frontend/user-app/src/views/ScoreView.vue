<template>
  <div class="page-container">
    <NavBar />

    <div class="balance-card">
      <div class="balance-label">当前积分</div>
      <div class="balance-num">{{ balance }}</div>
      <div class="balance-stats">
        <div class="stat-item earn">
          <span class="stat-label">累计获取</span>
          <span class="stat-value">+{{ summary.total_earn || 0 }}</span>
        </div>
        <div class="stat-item consume">
          <span class="stat-label">累计消耗</span>
          <span class="stat-value">-{{ summary.total_consume || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="tabs">
      <button
        :class="['tab-btn', { active: activeType === '' }]"
        @click="switchType('')"
      >
        全部
      </button>
      <button
        :class="['tab-btn', { active: activeType === 'earn' }]"
        @click="switchType('earn')"
      >
        获取
      </button>
      <button
        :class="['tab-btn', { active: activeType === 'consume' }]"
        @click="switchType('consume')"
      >
        消耗
      </button>
    </div>

    <div class="records-card">
      <div v-if="loading" class="loading-wrap">
        <div class="spinner"></div>
        <div>加载中...</div>
      </div>

      <div v-else-if="!records.length" class="empty-state">
        <div class="empty-icon">📋</div>
        <p>暂无积分记录</p>
      </div>

      <div v-else class="record-list">
        <div v-for="r in records" :key="r.id" class="record-item">
          <div class="record-left">
            <div class="record-desc">{{ r.description }}</div>
            <div class="record-time">{{ formatTime(r.create_time) }}</div>
          </div>
          <div :class="['record-score', r.type === 'earn' ? 'earn' : 'consume']">
            {{ r.type === 'earn' ? '+' : '' }}{{ r.score }}
          </div>
        </div>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button class="page-btn" :disabled="page <= 1" @click="goPage(page - 1)">
          上一页
        </button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button class="page-btn" :disabled="page >= totalPages" @click="goPage(page + 1)">
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import request from "../api/request";
import NavBar from "../components/NavBar.vue";

const balance = ref(0);
const summary = ref({ total_earn: 0, total_consume: 0 });
const records = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const activeType = ref("");
const loading = ref(false);

const pageSize = 20;
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 0);

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

async function loadBalance() {
  try {
    const res = await request.get("/api/score/balance");
    balance.value = res.data.data?.balance ?? 0;
  } catch {
    balance.value = 0;
  }
}

async function loadSummary() {
  try {
    const res = await request.get("/api/score/summary");
    summary.value = res.data.data || { total_earn: 0, total_consume: 0 };
  } catch {}
}

async function loadRecords() {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (activeType.value) {
      params.type = activeType.value;
    }
    const res = await request.get("/api/score/records", { params });
    const data = res.data.data || {};
    records.value = data.items || [];
    total.value = data.total || 0;
  } catch {
    records.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function switchType(type: string) {
  activeType.value = type;
  page.value = 1;
  loadRecords();
}

function goPage(p: number) {
  page.value = p;
  loadRecords();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onMounted(() => {
  loadBalance();
  loadSummary();
  loadRecords();
});
</script>

<style scoped>

.balance-card {
  background: linear-gradient(135deg, #f57f17 0%, #ff8f00 100%);
  border-radius: var(--radius);
  padding: 36px 40px;
  margin-bottom: 24px;
  color: white;
  text-align: center;
  box-shadow: var(--shadow-hover);
}
.balance-label {
  font-size: 14px;
  opacity: 0.85;
  margin-bottom: 8px;
}
.balance-num {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 20px;
}
.balance-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-label {
  font-size: 12px;
  opacity: 0.75;
}
.stat-value {
  font-size: 18px;
  font-weight: 700;
}
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.tab-btn {
  padding: 10px 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.tab-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary-light);
}
.tab-btn.active {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
  border-color: var(--primary);
}
.records-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
}
.record-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  transition: all 0.2s;
  border-radius: var(--radius-sm);
}
.record-item:hover {
  background: var(--primary-bg);
}
.record-item:last-child {
  border-bottom: none;
}
.record-left {
  flex: 1;
}
.record-desc {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.record-time {
  font-size: 12px;
  color: var(--text-muted);
}
.record-score {
  font-size: 18px;
  font-weight: 800;
  white-space: nowrap;
  margin-left: 16px;
}
.record-score.earn {
  color: #2e7d32;
}
.record-score.consume {
  color: #c62828;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.page-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.page-btn:hover:not(:disabled) {
  background: var(--primary-bg);
  border-color: var(--primary-light);
  color: var(--primary-dark);
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-info {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
}
.loading-wrap {
  text-align: center;
  padding: 60px;
  color: var(--primary);
}
.spinner {
  display: inline-block;
  width: 36px;
  height: 36px;
  border: 3px solid rgba(33, 150, 243, 0.15);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
