<template>
  <div class="page-container">
    <NavBar />

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载中...</div>
    </div>

    <div v-else-if="gift" class="detail-container">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="$router.back()">← 返回列表</button>

      <div class="detail-content">
        <!-- 左侧大图 -->
        <div class="image-section">
          <img :src="gift.image" :alt="gift.name" />
          <span class="stock-info">库存剩余：{{ gift.stock }} 件</span>
        </div>

        <!-- 右侧信息 -->
        <div class="info-section">
          <span class="category-tag">{{ gift.category }}</span>
          <h1>{{ gift.name }}</h1>
          <p class="desc">{{ gift.description }}</p>

          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">所需积分</span>
              <span class="meta-value points">{{ gift.points_required }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">现金价格</span>
              <span class="meta-value price">¥{{ gift.price }}</span>
            </div>
          </div>

          <!-- 兑换操作 -->
          <div class="action-area">
            <div v-if="gift.stock === 0" class="sold-out">已售罄</div>

            <template v-else>
              <div class="balance-info">
                您的积分余额：<strong>{{ userBalance }}</strong>
              </div>

              <div class="exchange-options">
                <label class="option" :class="{ disabled: !canExchange }">
                  <input type="radio" v-model="payMode" value="points" :disabled="!canExchange" />
                  <span class="option-main">积分兑换</span>
                  <span class="option-sub">消耗 {{ gift.points_required }} 积分</span>
                  <span v-if="!canExchange" class="hint">积分不足</span>
                </label>
                <label class="option">
                  <input type="radio" v-model="payMode" value="cash" />
                  <span class="option-main">直接购买</span>
                  <span class="option-sub">¥{{ gift.price }}</span>
                </label>
              </div>

              <button class="action-btn" @click="showConfirm = true" :disabled="submitting">
                {{ payMode === 'points' ? '积分兑换' : '¥' + (gift?.price ?? 0) + ' 直接购买' }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading-wrap">礼品不存在</div>

    <!-- 确认弹窗 -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="showConfirm = false">
      <div class="modal-card">
        <h3>确认下单</h3>
        <div class="modal-body">
          <p><strong>礼品：</strong>{{ gift?.name }}</p>
          <p><strong>数量：</strong>1 件</p>
          <p v-if="payMode === 'points'">
            <strong>消耗积分：</strong>{{ gift?.points_required }}
          </p>
          <p v-else>
            <strong>支付金额：</strong>¥{{ gift?.price }}
          </p>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showConfirm = false">取消</button>
          <button class="btn-confirm" @click="doOrder" :disabled="submitting">
            {{ submitting ? "提交中..." : "确认下单" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { giftApi, type GiftItem } from "../api/gift";
import { orderApi } from "../api/order";
import { useUserStore } from "../stores/user";
import NavBar from "../components/NavBar.vue";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const gift = ref<GiftItem | null>(null);
const loading = ref(true);
const showConfirm = ref(false);
const submitting = ref(false);
const payMode = ref<'points' | 'cash'>('points');

const userBalance = computed(() => userStore.userInfo?.score_balance ?? 0);
const canExchange = computed(() => userBalance.value >= (gift.value?.points_required ?? 0));

async function loadGift() {
  loading.value = true;
  try {
    const id = Number(route.params.id);
    const res = await giftApi.detail(id);
    gift.value = res.data.data;
  } finally {
    loading.value = false;
  }
}

async function doOrder() {
  if (!gift.value) return;
  submitting.value = true;
  try {
    const res = await orderApi.create({
      gift_id: gift.value.id,
      quantity: 1,
      use_points: payMode.value === 'points',
    });
    showConfirm.value = false;

    // 消耗积分后从服务端刷新积分余额
    if (payMode.value === 'points') {
      await userStore.fetchUserInfo();
    }

    alert(res.data.message || "下单成功！");
    alert(`下单成功！\n订单号：${res.data.data.order_no}\n请尽快完成支付`);
        router.push('/orders');
  } catch (e: any) {
    const detail = e?.response?.data?.detail;
    let errMsg = "下单失败，请重试";
    if (typeof detail === "string") {
      errMsg = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      errMsg = detail.map((d: any) => d.msg).join("; ");
    }
    alert(errMsg);
  } finally {
    submitting.value = false;
  }
}

onMounted(loadGift);
</script>

<style scoped>

.loading-wrap {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 15px;
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

.back-btn {
  background: none;
  border: none;
  color: var(--primary-dark);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  margin-bottom: 20px;
  font-weight: 600;
}
.back-btn:hover {
  color: var(--primary);
}

.detail-content {
  display: flex;
  gap: 40px;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
@media (max-width: 768px) {
  .detail-content {
    flex-direction: column;
    gap: 24px;
  }
}

.image-section {
  flex: 0 0 360px;
  text-align: center;
}
.image-section img {
  width: 100%;
  border-radius: 12px;
  background: var(--border);
}
.stock-info {
  display: inline-block;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-muted);
}

.info-section {
  flex: 1;
}
.category-tag {
  display: inline-block;
  background: var(--primary-bg);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
  margin-bottom: 12px;
}
.info-section h1 {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 12px;
}
.desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 24px;
}

.meta-row {
  display: flex;
  gap: 32px;
  margin-bottom: 28px;
  padding: 18px;
  background: var(--primary-bg);
  border-radius: 12px;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-label {
  font-size: 12px;
  color: var(--text-muted);
}
.meta-value {
  font-size: 22px;
  font-weight: 800;
}
.meta-value.points {
  color: #e65100;
}
.meta-value.price {
  color: var(--primary-dark);
}

.action-area {
  padding: 20px;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
}
.balance-info {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.balance-info strong {
  color: #e65100;
  font-size: 16px;
}
.exchange-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}
.option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border: 2px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
  background: var(--surface);
}
.option:has(input:checked) {
  border-color: var(--primary);
  background: var(--primary-bg);
}
.option.disabled {
  opacity: 0.45;
  cursor: not-allowed;
  background: #f5f5f5;
}
.option input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  flex-shrink: 0;
}
.option-main {
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary);
}
.option-sub {
  font-size: 13px;
  color: var(--text-muted);
}
.option .hint {
  font-size: 12px;
  color: #e65100;
  font-weight: 600;
  margin-left: auto;
}
.action-btn {
  width: 100%;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.sold-out {
  background: var(--border);
  color: var(--text-muted);
  text-align: center;
  padding: 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-card {
  background: var(--surface);
  border-radius: 14px;
  padding: 28px 32px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}
.modal-card h3 {
  margin: 0 0 18px;
  font-size: 18px;
  color: var(--text-primary);
}
.modal-body p {
  margin: 8px 0;
  font-size: 14px;
}
.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 22px;
  justify-content: flex-end;
}
.btn-cancel {
  padding: 10px 24px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
}
.btn-confirm {
  padding: 10px 24px;
  border: none;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}
.btn-confirm:hover:not(:disabled) {
  transform: translateY(-2px);
}
</style>
