<template>
  <div class="page-container">
    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>处理支付宝授权回调...</div>
    </div>
    <div v-else-if="success" class="result-card success">
      <div class="result-icon">✅</div>
      <h2>授权成功</h2>
      <p>支付宝账号已绑定</p>
      <p class="hint">窗口将在 3 秒后自动关闭</p>
    </div>
    <div v-else class="result-card fail">
      <div class="result-icon">❌</div>
      <h2>授权失败</h2>
      <p>{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { alipayApi } from "../api/alipay";

const route = useRoute();
const loading = ref(true);
const success = ref(false);
const errorMsg = ref("");

onMounted(async () => {
  const authCode = route.query.auth_code as string;
  const state = route.query.state as string;
  if (!authCode) {
    loading.value = false;
    errorMsg.value = "缺少授权码参数";
    return;
  }
  try {
    await alipayApi.callback(authCode, state);
    success.value = true;
    setTimeout(() => {
      window.close();
    }, 3000);
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || "授权处理失败";
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.result-card {
  max-width: 420px;
  margin: 80px auto;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 40px;
  text-align: center;
  box-shadow: var(--shadow);
}
.result-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.result-card h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}
.result-card p {
  color: var(--text-secondary);
  font-size: 14px;
}
.hint {
  font-size: 12px !important;
  color: var(--text-muted) !important;
  margin-top: 12px;
}
.fail h2 {
  color: #c62828;
}
.loading-wrap {
  text-align: center;
  padding: 80px;
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
</style>
