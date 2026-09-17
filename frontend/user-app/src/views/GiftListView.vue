<template>
  <div class="page-container">
    <NavBar />

    <h2 class="page-title">🎁 限量周边</h2>

    <!-- 分类筛选 -->
    <div class="filter-bar">
      <button
        v-for="cat in categories"
        :key="cat.value"
        :class="['filter-tag', { active: activeCategory === cat.value }]"
        @click="activeCategory = cat.value"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载中...</div>
    </div>

    <!-- 礼品网格 -->
    <div v-else class="gift-grid">
      <div
        v-for="gift in filteredGifts"
        :key="gift.id"
        class="gift-card"
        @click="goDetail(gift.id)"
      >
        <div class="card-body">
          <h3>{{ gift.name }}</h3>
          <p class="card-desc">{{ gift.description }}</p>
          <div class="card-footer">
            <span class="points-tag">{{ gift.points_required }} 积分</span>
            <span class="price-tag" v-if="gift.price > 0">¥{{ gift.price }}</span>
            <span class="stock-tag">库存 {{ gift.stock }}</span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredGifts.length === 0" class="empty-state">
        暂无该分类的礼品
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { giftApi, type GiftItem } from "../api/gift";
import NavBar from "../components/NavBar.vue";

const router = useRouter();
const gifts = ref<GiftItem[]>([]);
const loading = ref(true);
const activeCategory = ref("");

const categories = [
  { label: "全部", value: "" },
  { label: "联名款", value: "联名款" },
  { label: "限定款", value: "限定款" },
  { label: "盲盒", value: "盲盒" },
];

const filteredGifts = computed(() => {
  if (!activeCategory.value) return gifts.value;
  return gifts.value.filter((g) => g.category === activeCategory.value);
});

async function loadGifts() {
  loading.value = true;
  try {
    const res = await giftApi.list();
    gifts.value = res.data.data.items;
  } finally {
    loading.value = false;
  }
}

function goDetail(id: number) {
  router.push(`/gifts/${id}`);
}

onMounted(loadGifts);
</script>

<style scoped>

.page-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 20px;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-tag {
  padding: 8px 20px;
  border-radius: 24px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.filter-tag:hover,
.filter-tag.active {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: #fff;
  border-color: transparent;
}

/* 网格 */
.gift-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
@media (max-width: 640px) {
  .gift-grid {
    grid-template-columns: 1fr;
  }
}

/* 卡片 */
.gift-card {
  background: var(--surface);
  border-radius: var(--radius);
  cursor: pointer;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: transform 0.3s, box-shadow 0.3s;
}
.gift-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}
.card-body {
  padding: 18px 20px;
}
.card-body h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}
.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-footer {
  display: flex;
  gap: 10px;
  align-items: center;
}
.points-tag {
  background: var(--primary-bg);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
}
.price-tag {
  font-size: 13px;
  color: var(--text-muted);
}
.stock-tag {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
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
  to { transform: rotate(360deg); }
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 15px;
}
</style>
