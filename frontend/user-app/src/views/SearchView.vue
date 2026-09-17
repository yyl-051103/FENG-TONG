<template>
  <div class="page-container">
    <NavBar />

    <div class="search-section">
      <div class="search-box">
        <input
          type="text"
          class="search-input"
          v-model="keyword"
          placeholder="搜索新闻标题或内容..."
          @keypress.enter="doSearch()"
        />
        <button class="search-btn" @click="doSearch()">🔍 搜索</button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>正在搜索...</div>
    </div>

    <div v-else-if="searched && !results.length" class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>未找到相关结果</h3>
      <p>请尝试其他关键词</p>
    </div>

    <div v-else-if="results.length" class="results-section">
      <div class="results-header">
        搜索 "<strong>{{ lastQuery }}</strong>" 共找到 <strong>{{ total }}</strong> 条结果
      </div>
      <div class="result-list">
        <div v-for="item in results" :key="item.id" class="result-item" @click="goDetail(item.id)">
          <div class="result-title" v-html="item.title"></div>
          <div class="result-summary" v-html="item.content"></div>
          <div class="result-meta">
            <span>{{ item.author || '未知作者' }}</span>
            <span>{{ formatTime(item.create_time) }}</span>
          </div>
        </div>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button
          class="page-btn"
          :disabled="page <= 1"
          @click="goPage(page - 1)"
        >
          上一页
        </button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button
          class="page-btn"
          :disabled="page >= totalPages"
          @click="goPage(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import request from "../api/request";
import NavBar from "../components/NavBar.vue";

const route = useRoute();
const router = useRouter();

const keyword = ref("");
const results = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const loading = ref(false);
const searched = ref(false);
const lastQuery = ref("");

const pageSize = 20;
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 0);

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

async function doSearch(p?: number) {
  const q = keyword.value.trim();
  if (!q) return;

  const targetPage = p ?? 1;
  page.value = targetPage;
  lastQuery.value = q;
  loading.value = true;
  searched.value = true;

  try {
    const res = await request.get("/api/search/news", {
      params: { q, page: targetPage },
    });
    const data = res.data.data || {};
    results.value = data.items || [];
    total.value = data.total || 0;
  } catch {
    results.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function goPage(p: number) {
  doSearch(p);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function goDetail(id: number) {
  router.push(`/news/${id}`);
}

onMounted(() => {
  const q = (route.query.q as string) || "";
  if (q) {
    keyword.value = q;
    doSearch();
  }
});

watch(
  () => route.query.q,
  (newQ) => {
    if (newQ && typeof newQ === "string") {
      keyword.value = newQ;
      doSearch();
    }
  }
);
</script>

<style scoped>

.search-section {
  margin-bottom: 28px;
}
.search-box {
  display: flex;
  gap: 12px;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 16px 20px;
  box-shadow: var(--shadow);
}
.search-input {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s;
}
.search-input:focus {
  border-color: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}
.search-btn {
  padding: 12px 28px;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}
.results-section {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
}
.results-header {
  font-size: 14px;
  color: var(--text-secondary);
  padding-bottom: 16px;
  border-bottom: 2px solid var(--border);
  margin-bottom: 16px;
}
.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-item {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.3s;
}
.result-item:hover {
  border-color: var(--primary-light);
  box-shadow: 0 2px 12px rgba(33, 150, 243, 0.1);
  transform: translateY(-2px);
}
.result-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  line-height: 1.4;
}
.result-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 12px;
}
.result-meta {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
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
  padding: 80px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
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
@media (max-width: 768px) {
  .search-box {
    flex-direction: column;
  }
}
</style>
