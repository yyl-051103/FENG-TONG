<template>
  <div class="page-container">
    <NavBar />

    <div class="flash-header">
      <h1>⚡ 限时抢购</h1>
      <div v-if="nextSale" class="countdown-bar">
        <span v-if="nextSale.status === '未开始'">
          距「{{ nextSale.gift_name }}」开始：
          <strong>{{ countdownText }}</strong>
        </span>
        <span v-else-if="nextSale.status === '进行中'">
          抢购进行中！距结束：<strong>{{ countdownText }}</strong>
        </span>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载中...</div>
    </div>

    <div v-else-if="!items.length" class="empty-state">
      暂无抢购活动，敬请期待
    </div>

    <div v-else class="flash-grid">
      <div
        v-for="item in resolvedItems"
        :key="item.id"
        class="flash-card"
        :class="{ active: item.status === '进行中', ended: item.status === '已结束' }"
      >
        <div class="flash-status-badge" :class="item.status">
          {{ statusLabel(item.status) }}
        </div>
        <div class="flash-image-wrap">
          <img
            v-if="item.gift_image"
            :src="item.gift_image"
            :alt="item.gift_name"
            class="flash-image"
          />
          <div v-else class="flash-image-placeholder">🎁</div>
        </div>
        <div class="flash-info">
          <h3 class="flash-name">{{ item.gift_name }}</h3>
          <p class="flash-desc">{{ item.gift_description }}</p>
          <div class="flash-price-row">
            <span v-if="item.flash_price_points > 0" class="flash-price-points">
              💰 {{ item.flash_price_points }} 积分
            </span>
            <span v-if="item.flash_price_cash > 0" class="flash-price-cash">
              ¥{{ item.flash_price_cash.toFixed(2) }}
            </span>
            <span v-if="item.flash_price_points === 0 && item.flash_price_cash === 0" class="flash-price-cash">
              免费
            </span>
          </div>
          <div class="stock-bar-wrap">
            <div class="stock-bar">
              <div
                class="stock-bar-fill"
                :style="{ width: stockPercent(item) + '%' }"
              ></div>
            </div>
            <span class="stock-text">
              剩余 {{ item.current_stock }} / {{ item.flash_stock }}
            </span>
          </div>
          <button
            class="flash-btn"
            :disabled="item.status !== '进行中' || item.current_stock <= 0"
            @click="doBuy(item)"
          >
            <template v-if="item.status === '未开始'">未开始</template>
            <template v-else-if="item.status === '已结束'">已结束</template>
            <template v-else-if="item.current_stock <= 0">已售罄</template>
            <template v-else>立即抢购</template>
          </button>
        </div>
      </div>
    </div>

    <!-- 排队弹窗 -->
    <div v-if="showQueueModal" class="modal-overlay">
      <div class="modal-box">
        <div class="spinner"></div>
        <p>排队中，请稍候...</p>
        <p class="queue-hint">正在为您分配库存</p>
        <button class="btn-cancel" @click="cancelQueue">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import NavBar from "../components/NavBar.vue";
import { flashSaleApi, type FlashSaleItem } from "../api/flash-sale";
import { orderApi } from "../api/order";
import { useUserStore } from "../stores/user";

const router = useRouter();
const userStore = useUserStore();

const items = ref<FlashSaleItem[]>([]);
const loading = ref(true);
/** 服务端时间与客户端时间的偏移量（毫秒）：serverTime(ms) - Date.now() */
const serverTimeOffset = ref(0);
const showQueueModal = ref(false);
const now = ref(Date.now());
let pollTimer: ReturnType<typeof setInterval> | null = null;
let countdownTimer: ReturnType<typeof setInterval> | null = null;
let queueTimer: ReturnType<typeof setInterval> | null = null;

/** 根据服务端时间偏移推算当前服务端时间戳（秒） */
function serverNowSec(): number {
  return (Date.now() + serverTimeOffset.value) / 1000;
}

/** 根据服务端时间判定单项的实际状态（覆盖后端可能滞后的 status） */
function resolveStatus(item: FlashSaleItem): string {
  const srv = serverNowSec();
  if (srv < item.start_time) return "未开始";
  if (srv < item.end_time) return "进行中";
  return "已结束";
}

const nextSale = computed(() => {
  // 强制依赖 now 以每秒重算
  void now.value;
  const srv = serverNowSec();
  // 先找进行中的
  const active = items.value.find((i) => srv >= i.start_time && srv < i.end_time);
  if (active) return { ...active, status: "进行中" };
  // 再找即将开始的（距开始最近的）
  const upcoming = items.value
    .filter((i) => srv < i.start_time)
    .sort((a, b) => a.start_time - b.start_time);
  if (upcoming.length) return { ...upcoming[0], status: "未开始" };
  return null;
});

/** 格式化倒计时：>=24h 显示 X天 HH:mm:ss，否则 HH:mm:ss */
function formatCountdown(diffMs: number): string {
  if (diffMs <= 0) return "00:00:00";
  const totalSec = Math.floor(diffMs / 1000);
  const d = Math.floor(totalSec / 86400);
  const h = Math.floor((totalSec % 86400) / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  if (d > 0) return `${d}天 ${pad(h)}:${pad(m)}:${pad(s)}`;
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

const countdownText = computed(() => {
  if (!nextSale.value) return "";
  void now.value;
  const srv = serverNowSec();
  const targetSec =
    nextSale.value.status === "未开始"
      ? nextSale.value.start_time
      : nextSale.value.end_time;
  const diffMs = (targetSec - srv) * 1000;
  return formatCountdown(diffMs);
});

function statusLabel(s: string) {
  const map: Record<string, string> = {
    "未开始": "即将开始",
    "进行中": "抢购中",
    "已结束": "已结束",
  };
  return map[s] || s;
}

function stockPercent(item: FlashSaleItem) {
  if (item.flash_stock <= 0) return 0;
  return Math.max(0, (item.current_stock / item.flash_stock) * 100);
}

async function loadData() {
  loading.value = true;
  try {
    const res = await flashSaleApi.list();
    const data = res.data.data;
    items.value = data.items;
    // 计算偏移：服务端时间戳（秒）→ 毫秒，减去客户端当前时间
    serverTimeOffset.value = data.server_time * 1000 - Date.now();
  } catch (e) {
    console.error("[FlashSale] 加载失败:", e);
  } finally {
    loading.value = false;
  }
}

/** 对应当前秒刷新的 items 视图，含实时状态 */
const resolvedItems = computed(() => {
  void now.value;
  return items.value.map((item) => ({
    ...item,
    status: resolveStatus(item),
  }));
});

async function doBuy(item: FlashSaleItem) {
  showQueueModal.value = true;
  try {
    const res = await orderApi.create({ gift_id: item.gift_id, quantity: 1, flash_sale_id: item.id });
    const result = res.data.data;
    // 消耗积分时刷新 store 中的积分余额
    if (item.flash_price_points > 0) {
      userStore.fetchUserInfo();
    }
    if ((result as any).status === "queuing") {
      pollResult();
    } else {
      showQueueModal.value = false;
      router.push(`/checkout/${result.order_no}`);
    }
  } catch (e: any) {
    showQueueModal.value = false;
    alert(e?.response?.data?.detail || "抢购失败");
  }
}

function pollResult() {
  queueTimer = setInterval(async () => {
    try {
      const res = await orderApi.getResult();
      const result = res.data.data;
      if (result.status !== "queuing") {
        clearInterval(queueTimer!);
        queueTimer = null;
        showQueueModal.value = false;
        if (result.success) {
          router.push(`/checkout/${result.order_no}`);
        } else {
          alert(result.reason || "抢购失败");
        }
      }
    } catch {
      // keep polling
    }
  }, 1000);
}

function cancelQueue() {
  if (queueTimer) {
    clearInterval(queueTimer);
    queueTimer = null;
  }
  showQueueModal.value = false;
}

onMounted(() => {
  loadData();
  countdownTimer = setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer);
  if (pollTimer) clearInterval(pollTimer);
  if (queueTimer) clearInterval(queueTimer);
});
</script>

<style scoped>
.flash-header {
  text-align: center;
  margin-bottom: 32px;
}
.flash-header h1 {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #ff6f00, #e65100);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}
.countdown-bar {
  font-size: 18px;
  color: var(--text-secondary);
}
.countdown-bar strong {
  color: #e65100;
  font-size: 24px;
  font-family: "Courier New", monospace;
}
.flash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}
.flash-card {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  position: relative;
  transition: all 0.3s;
  border: 2px solid transparent;
}
.flash-card.active {
  border-color: #ff6f00;
  box-shadow: 0 0 20px rgba(255, 111, 0, 0.15);
}
.flash-card.ended {
  opacity: 0.7;
}
.flash-status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  z-index: 1;
}
.flash-status-badge.进行中 {
  background: #ff6f00;
  color: white;
}
.flash-status-badge.未开始 {
  background: #e3f2fd;
  color: #1565c0;
}
.flash-status-badge.已结束 {
  background: #eee;
  color: #999;
}
.flash-image-wrap {
  width: 100%;
  height: 200px;
  background: var(--primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.flash-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.flash-image-placeholder {
  font-size: 64px;
}
.flash-info {
  padding: 16px;
}
.flash-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}
.flash-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.flash-price-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.flash-price-points {
  font-size: 16px;
  font-weight: 700;
  color: #f57f17;
}
.flash-price-cash {
  font-size: 20px;
  font-weight: 800;
  color: #e65100;
}
.stock-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.stock-bar {
  flex: 1;
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}
.stock-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6f00, #ffab40);
  border-radius: 4px;
  transition: width 0.3s;
}
.stock-text {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}
.flash-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #ff6f00, #e65100);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.flash-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(255, 111, 0, 0.4);
}
.flash-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: white;
  border-radius: var(--radius);
  padding: 40px;
  text-align: center;
  min-width: 300px;
}
.modal-box .spinner {
  margin: 0 auto 16px;
}
.queue-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.btn-cancel {
  padding: 8px 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: white;
  cursor: pointer;
  color: var(--text-secondary);
}
.loading-wrap {
  text-align: center;
  padding: 60px;
  color: var(--primary);
}
.spinner {
  display: inline-block;
  width: 32px;
  height: 32px;
  border: 3px solid rgba(33, 150, 243, 0.15);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.empty-state {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
  font-size: 16px;
}
</style>
