<template>
  <div class="page-container">
    <NavBar />

    <h2 class="page-title">📦 我的订单</h2>

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载中...</div>
    </div>

    <div v-else-if="orders.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <p>还没有订单</p>
      <router-link to="/gifts" class="go-link">去兑换礼品</router-link>
    </div>

    <div v-else class="order-list">
      <div v-for="order in orders" :key="order.id" class="order-card">
        <div class="order-header">
          <span class="order-no">订单号：{{ order.order_no }}</span>
          <span :class="['status-tag', order.status === '待支付' ? 'pending' : '', order.status === '已支付' ? 'paid' : '']">
            {{ order.status }}
          </span>
        </div>

        <div class="order-body">
          <div class="order-items">
            <div v-for="item in order.items" :key="item.gift_name" class="order-item">
              <span class="item-name">{{ item.gift_name }}</span>
              <span class="item-qty">x{{ item.quantity }}</span>
            </div>
          </div>

          <div class="order-summary">
            <div v-if="order.total_points > 0" class="summary-row">
              <span>消耗积分</span>
              <span class="val points">{{ order.total_points }}</span>
            </div>
            <div v-if="order.total_price > 0" class="summary-row">
              <span>支付金额</span>
              <span class="val price">¥{{ order.total_price }}</span>
            </div>
          </div>
        </div>

        <div class="order-footer">
          <span class="order-time">{{ formatTime(order.create_time) }}</span>
          <div class="footer-actions">
            <span
              v-if="order.status === '待支付' && order.expire_time"
              class="countdown-text"
              :class="{ 'countdown-urgent': getRemainingSeconds(order) <= 60 && getRemainingSeconds(order) > 0, 'countdown-expired': getRemainingSeconds(order) <= 0 }"
            >{{ getCountdownText(order) }}</span>
            <button
              v-if="order.status === '待支付' && order.total_price > 0"
              class="pay-btn"
              @click="goPay(order)"
            >
              去支付
            </button>
            <button
              v-if="order.status === '待支付'"
              class="cancel-btn"
              :disabled="cancelling === order.id"
              @click="handleCancel(order)"
            >
              {{ cancelling === order.id ? '取消中...' : '取消订单' }}
            </button>
            <button
              v-if="['已支付', '已完成', '已取消'].includes(order.status)"
              class="delete-btn"
              :class="{ 'delete-btn-danger': order.status === '已支付' || order.status === '已完成' }"
              :disabled="deleting === order.id"
              @click="handleDelete(order)"
            >
              {{ deleting === order.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 取消确认弹窗 -->
    <div v-if="confirmVisible" class="modal-overlay" @click.self="confirmVisible = false">
      <div class="modal-box">
        <p class="modal-text">确定要取消订单 <strong>{{ pendingCancel?.order_no }}</strong> 吗？</p>
        <p class="modal-hint">取消后将恢复礼品库存并退还积分。</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="confirmVisible = false">再想想</button>
          <button class="btn-danger" @click="doCancel">确认取消</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="deleteConfirmVisible" class="modal-overlay" @click.self="deleteConfirmVisible = false">
      <div class="modal-box">
        <p class="modal-text">确定要删除订单 <strong>{{ pendingDelete?.order_no }}</strong> 吗？</p>
        <p v-if="pendingDelete?.status === '已支付' || pendingDelete?.status === '已完成'" class="modal-warning">
          此订单已支付，删除后积分和金额不会退回，且不可恢复。确定要删除吗？
        </p>
        <p v-else class="modal-hint">删除后不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="deleteConfirmVisible = false">再想想</button>
          <button class="btn-danger" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { orderApi, type OrderData } from "../api/order";
import { useUserStore } from "../stores/user";
import NavBar from "../components/NavBar.vue";

const router = useRouter();
const userStore = useUserStore();

const orders = ref<OrderData[]>([]);
const now = ref(Date.now());
let countdownTimer: ReturnType<typeof setInterval> | null = null;
const loading = ref(true);
const cancelling = ref<number | null>(null);
const confirmVisible = ref(false);
const pendingCancel = ref<OrderData | null>(null);
const deleting = ref<number | null>(null);
const deleteConfirmVisible = ref(false);
const pendingDelete = ref<OrderData | null>(null);

async function loadOrders() {
  loading.value = true;
  try {
    const res = await orderApi.list();
    orders.value = res.data.data.items;
  } finally {
    loading.value = false;
  }
}

function goPay(order: OrderData) {
  router.push("/checkout/" + order.order_no);
}

function handleCancel(order: OrderData) {
  pendingCancel.value = order;
  confirmVisible.value = true;
}

async function doCancel() {
  if (!pendingCancel.value) return;
  const orderId = pendingCancel.value.id;
  cancelling.value = orderId;
  confirmVisible.value = false;
  try {
    await orderApi.cancel(orderId);
    // 取消订单可能退还积分，刷新 store 中的积分余额
    userStore.fetchUserInfo();
    await loadOrders();
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.message || "取消失败，请稍后重试");
  } finally {
    cancelling.value = null;
    pendingCancel.value = null;
  }
}

function handleDelete(order: OrderData) {
  pendingDelete.value = order;
  deleteConfirmVisible.value = true;
}

async function doDelete() {
  if (!pendingDelete.value) return;
  const orderId = pendingDelete.value.id;
  deleting.value = orderId;
  deleteConfirmVisible.value = false;
  try {
    await orderApi.delete(orderId);
    await loadOrders();
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.message || "删除失败，请稍后重试");
  } finally {
    deleting.value = null;
    pendingDelete.value = null;
  }
}

function getRemainingSeconds(order: OrderData): number {
  if (!order.expire_time) return -1;
  const expire = new Date(order.expire_time).getTime();
  return Math.max(0, Math.floor((expire - now.value) / 1000));
}

function getCountdownText(order: OrderData): string {
  const s = getRemainingSeconds(order);
  if (s <= 0) return '订单已超时';
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `剩余 ${m}分${sec.toString().padStart(2, '0')}秒`;
}

function formatTime(ts: string) {
  if (!ts) return "";
  const d = new Date(ts);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day} ${h}:${min}`;
}

onMounted(() => {
  loadOrders();
  countdownTimer = setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
});
</script>

<style scoped>

.page-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 24px;
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
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.go-link {
  display: inline-block;
  margin-top: 14px;
  color: var(--primary-dark);
  font-weight: 600;
  text-decoration: none;
  padding: 8px 22px;
  border-radius: 8px;
  background: var(--primary-bg);
}
.go-link:hover {
  background: var(--border);
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.order-no {
  font-size: 13px;
  color: var(--text-muted);
  font-family: monospace;
}
.status-tag {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 12px;
  background: #e8f5e9;
  color: #2e7d32;
}
.status-tag.pending {
  background: #fff3e0;
  color: #e65100;
}
.status-tag.paid {
  background: #ffebee;
  color: #c62828;
}

.order-body {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}
.order-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.order-item {
  display: flex;
  gap: 10px;
  font-size: 14px;
}
.item-name {
  color: var(--text-primary);
  font-weight: 600;
}
.item-qty {
  color: var(--text-muted);
}

.order-summary {
  text-align: right;
}
.summary-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--text-muted);
  align-items: center;
  margin-bottom: 4px;
}
.val {
  font-weight: 700;
  font-size: 15px;
}
.val.points {
  color: #e65100;
}
.val.price {
  color: var(--primary-dark);
}

.order-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.order-time {
  font-size: 12px;
  color: var(--text-muted);
}

.footer-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.countdown-text {
  font-size: 12px;
  font-weight: 600;
  color: #1565c0;
  background: #e3f2fd;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}
.countdown-urgent {
  color: #e65100;
  background: #fff3e0;
  animation: countdown-blink 1s infinite;
}
.countdown-expired {
  color: #c62828;
  background: #ffebee;
}
@keyframes countdown-blink {
  50% { opacity: 0.5; }
}

.pay-btn {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.pay-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.cancel-btn {
  font-size: 12px;
  font-weight: 600;
  color: #d32f2f;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.cancel-btn:hover:not(:disabled) {
  background: #ffcdd2;
  border-color: #ef9a9a;
}
.cancel-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.delete-btn {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.delete-btn:hover:not(:disabled) {
  color: #d32f2f;
  background: #ffebee;
  border-color: #ffcdd2;
}
.delete-btn-danger {
  color: #d32f2f;
  background: #ffebee;
  border-color: #ffcdd2;
}
.delete-btn-danger:hover:not(:disabled) {
  background: #ffcdd2;
  border-color: #ef9a9a;
}
.delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 确认弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}
.modal-text {
  font-size: 15px;
  color: #333;
  margin: 0 0 8px;
}
.modal-hint {
  font-size: 13px;
  color: #888;
  margin: 0 0 24px;
}
.modal-warning {
  font-size: 13px;
  color: #d32f2f;
  background: #fff5f5;
  border: 1px solid #ffcdd2;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 0 0 24px;
  font-weight: 600;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.btn-secondary {
  font-size: 13px;
  font-weight: 600;
  color: #555;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 20px;
  cursor: pointer;
}
.btn-secondary:hover {
  background: #e8e8e8;
}
.btn-danger {
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: #d32f2f;
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  cursor: pointer;
}
.btn-danger:hover {
  background: #b71c1c;
}
</style>
