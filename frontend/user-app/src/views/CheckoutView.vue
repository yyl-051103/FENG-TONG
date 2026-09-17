<template>
  <div class="page-container">
    <NavBar />

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载订单信息...</div>
    </div>

    <div v-else-if="!order" class="empty-state">订单不存在</div>

    <div v-else class="checkout-card">
      <h2>收银台</h2>
      <div class="order-info">
        <div class="info-row">
          <span class="info-label">订单号</span>
          <span class="info-value">{{ order.order_no }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">状态</span>
          <span class="info-value status-badge" :class="order.status">
            {{ order.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">礼品</span>
          <span class="info-value">
            <template v-for="(item, idx) in order.items" :key="idx">
              {{ item.gift_name }} x{{ item.quantity
              }}<template v-if="idx < order.items.length - 1">, </template>
            </template>
          </span>
        </div>
        <div v-if="order.total_points > 0" class="info-row">
          <span class="info-label">消耗积分</span>
          <span class="info-value points">{{ order.total_points }} 积分</span>
        </div>
        <div v-if="order.total_price > 0" class="info-row">
          <span class="info-label">支付金额</span>
          <span class="info-value price">¥{{ order.total_price.toFixed(2) }}</span>
        </div>
      </div>

      <!-- 待支付 + 金额>0：支付宝扫码支付按钮 -->
      <div v-if="order.status === '待支付' && order.total_price > 0" class="pay-section">
        <button class="pay-btn" @click="doAlipay" :disabled="paying">
          {{ paying ? "正在生成二维码..." : "支付宝扫码支付" }}
        </button>
      </div>

      <!-- 待支付 + 金额==0：纯积分兑换 -->
      <div v-if="order.status === '待支付' && order.total_price === 0" class="pay-section">
        <p class="points-hint">纯积分兑换，无需支付</p>
      </div>

      <!-- 已支付 -->
      <div v-if="order.status === '已支付'" class="pay-section success-section">
        <div class="success-icon">✅</div>
        <p class="success-text">支付成功！</p>
        <router-link to="/orders" class="back-link">查看我的订单</router-link>
      </div>

      <!-- 已取消 -->
      <div v-if="order.status === '已取消'" class="pay-section">
        <p class="cancelled-hint">订单已取消</p>
      </div>
    </div>

    <!-- 二维码弹窗 -->
    <div v-if="qrModalVisible" class="qr-modal-overlay" @click.self="closeQrModal">
      <div class="qr-modal">
        <h3>支付宝扫码支付</h3>
        <img v-if="qrDataUrl" :src="qrDataUrl" class="qr-image" alt="支付二维码" />
        <p v-else class="qr-loading">正在生成二维码...</p>
        <p class="qr-hint">请用支付宝App扫描二维码支付</p>
        <button class="close-btn" @click="closeQrModal">取消支付</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import NavBar from "../components/NavBar.vue";
import { orderApi, type OrderData } from "../api/order";
import { alipayApi } from "../api/alipay";

const route = useRoute();

const orderNo = route.params.orderNo as string;
const order = ref<OrderData | null>(null);
const loading = ref(true);
const paying = ref(false);

const qrModalVisible = ref(false);
const qrDataUrl = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function loadOrder() {
  try {
    const res = await orderApi.list();
    const orders: OrderData[] = res.data.data.items;
    const found = orders.find((o: OrderData) => o.order_no === orderNo) || null;
    if (!found) {
      order.value = null;
      return;
    }
    order.value = found;

    // 页面加载时若 DB 显示待支付，主动询问支付宝真实状态
    if (found.status === "待支付" && found.total_price > 0) {
      try {
        const statusRes = await alipayApi.queryOrderStatus(orderNo);
        if (statusRes.data.data.status === "已支付") {
          order.value.status = "已支付";
        }
      } catch { /* 忽略查询失败 */}
    }
  } catch (e) {
    console.error("[Checkout] 加载订单失败:", e);
  } finally {
    loading.value = false;
  }
}

async function doAlipay() {
  paying.value = true;
  try {
    const res = await alipayApi.prepay(orderNo);
    const data = res.data.data;

    // 支付宝已支付（前次支付成功但 DB 未同步，后端已补同步）
    if (data.already_paid) {
      if (order.value) order.value.status = "已支付";
      return;
    }

    const { qr_code } = data;
    const QRCode = (await import("qrcode")).default;
    qrDataUrl.value = await QRCode.toDataURL(qr_code);
    qrModalVisible.value = true;
    startPolling();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "生成支付二维码失败");
  } finally {
    paying.value = false;
  }
}

function startPolling() {
  let attempts = 0;
  const maxAttempts = 150; // 5 min
  pollTimer = setInterval(async () => {
    attempts++;
    try {
      const res = await alipayApi.queryOrderStatus(orderNo);
      if (res.data.data.status === "已支付") {
        clearPolling();
        qrModalVisible.value = false;
        if (order.value) order.value.status = "已支付";
        return;
      }
      if (attempts >= maxAttempts) {
        clearPolling();
        qrModalVisible.value = false;
        alert("支付超时（5分钟），请手动刷新页面查看订单状态");
      }
    } catch {
      // keep polling
    }
  }, 1000);
}

function clearPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function closeQrModal() {
  clearPolling();
  qrModalVisible.value = false;
}

onMounted(() => {
  loadOrder();
});

onUnmounted(() => {
  clearPolling();
});
</script>

<style scoped>
.checkout-card {
  max-width: 560px;
  margin: 0 auto;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
}
.checkout-card h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--border);
}
.order-info {
  margin-bottom: 24px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.info-label {
  color: var(--text-muted);
  font-size: 14px;
}
.info-value {
  font-weight: 600;
  font-size: 14px;
}
.info-value.points {
  color: #f57f17;
}
.info-value.price {
  color: #e65100;
  font-size: 20px;
}
.status-badge.待支付 {
  color: #f57f17;
  background: #fff8e1;
  padding: 2px 10px;
  border-radius: 12px;
}
.status-badge.已支付 {
  color: #2e7d32;
  background: #e8f5e9;
  padding: 2px 10px;
  border-radius: 12px;
}
.status-badge.已取消 {
  color: #9e9e9e;
  background: #f5f5f5;
  padding: 2px 10px;
  border-radius: 12px;
}
.pay-section {
  text-align: center;
}
.pay-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #1677ff, #0958d9);
  color: white;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.pay-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.4);
}
.pay-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.points-hint {
  font-size: 15px;
  color: #2e7d32;
  font-weight: 600;
  padding: 16px;
  background: #e8f5e9;
  border-radius: var(--radius-sm);
}
.cancelled-hint {
  font-size: 15px;
  color: #9e9e9e;
  font-weight: 600;
  padding: 16px;
  background: #f5f5f5;
  border-radius: var(--radius-sm);
}
.success-section {
  padding: 20px;
}
.success-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.success-text {
  font-size: 20px;
  font-weight: 700;
  color: #2e7d32;
  margin-bottom: 16px;
}
.back-link {
  color: var(--primary);
  font-weight: 600;
  text-decoration: none;
}
.back-link:hover {
  text-decoration: underline;
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
  margin-bottom: 12px;
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
}

/* QR Modal */
.qr-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.qr-modal {
  background: white;
  border-radius: var(--radius);
  padding: 32px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.qr-modal h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}
.qr-image {
  width: 200px;
  height: 200px;
  margin-bottom: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.qr-loading {
  width: 200px;
  height: 200px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}
.qr-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}
.close-btn {
  padding: 8px 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.close-btn:hover {
  background: #f5f5f5;
}
</style>
