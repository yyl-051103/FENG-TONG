<template>
<div class="login-page">
<div class="login-card">
<div class="logo-area">
<div class="logo-icon">🛡️</div>
<div class="logo-title">智能风控新闻平台</div>
<div class="logo-subtitle">AI创作辅助 × 智能风控审核 × 安全内容生态</div>
</div>

<div v-if="alertMsg" :class="['alert', alertType]">{{ alertMsg }}</div>

<form id="loginForm" onsubmit="return false;">
<div class="form-group">
<label class="form-label">账号</label>
<input type="text" class="form-input" v-model="username" placeholder="请输入账号" autocomplete="username">
</div>
<div class="form-group">
<label class="form-label">密码</label>
<input type="password" class="form-input" v-model="password" placeholder="请输入密码" autocomplete="current-password" @keypress="onKeyPress">
</div>
<button type="button" class="btn btn-primary" @click="doLogin">
<span>🔐</span> 登录
</button>
</form>

<div class="divider"><span>或</span></div>

<div class="phone-login-section">
  <div class="form-group">
    <label class="form-label">手机号</label>
    <input type="tel" class="form-input" v-model="phone" placeholder="请输入手机号" maxlength="11">
  </div>
  <div class="form-group sms-row">
    <input type="text" class="form-input sms-input" v-model="smsCode" placeholder="验证码" maxlength="6" @keypress="onSmsKeyPress">
    <button type="button" class="btn-sms" @click="sendSms" :disabled="smsCountdown > 0">
      {{ smsCountdown > 0 ? smsCountdown + 's后重发' : '获取验证码' }}
    </button>
  </div>
  <button type="button" class="btn btn-phone" @click="doPhoneLogin">手机号验证码登录</button>
</div>

<button type="button" class="btn btn-secondary" @click="goRegister">
<span>📝</span> 注册新账号
</button>

<div class="footer-link">
还没有账号？<router-link to="/register">立即注册</router-link>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../stores/user";
import { authApi } from "../api/auth";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const username = ref("");
const password = ref("");
const phone = ref("");
const smsCode = ref("");
const smsCountdown = ref(0);
let smsTimer: ReturnType<typeof setInterval> | null = null;
const alertMsg = ref("");
const alertType = ref("alert-danger");

function getRedirectPath(): string {
  const redirect = route.query.redirect;
  if (typeof redirect === "string" && redirect.startsWith("/")) {
    return redirect;
  }
  return userStore.isAdmin ? "/news/create" : "/";
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    router.replace(getRedirectPath());
  }
});

function showAlert(msg: string, type: string) {
  alertMsg.value = msg;
  alertType.value = "alert-" + type;
  setTimeout(() => { alertMsg.value = ""; }, 4000);
}

async function doLogin() {
  const u = username.value.trim();
  const p = password.value.trim();

  if (!u) { showAlert("请输入账号", "danger"); return; }
  if (!p) { showAlert("请输入密码", "danger"); return; }

  try {
    await userStore.login(u, p);
    showAlert("登录成功，正在跳转...", "success");
    setTimeout(() => {
      router.replace(getRedirectPath());
    }, 800);
  } catch (err: any) {
    showAlert("登录失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

async function sendSms() {
  const p = phone.value.trim();
  if (!p || p.length !== 11) { showAlert("请输入正确的手机号", "danger"); return; }
  try {
    await authApi.sendSms({ phone: p });
    showAlert("验证码已发送", "success");
    smsCountdown.value = 60;
    smsTimer = setInterval(() => {
      smsCountdown.value--;
      if (smsCountdown.value <= 0 && smsTimer) { clearInterval(smsTimer); smsTimer = null; }
    }, 1000);
  } catch (err: any) {
    showAlert("发送失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

async function doPhoneLogin() {
  const p = phone.value.trim();
  const c = smsCode.value.trim();
  if (!p || p.length !== 11) { showAlert("请输入正确的手机号", "danger"); return; }
  if (!c) { showAlert("请输入验证码", "danger"); return; }
  try {
    await userStore.phoneLogin(p, c);
    showAlert("登录成功，正在跳转...", "success");
    setTimeout(() => { router.replace(getRedirectPath()); }, 800);
  } catch (err: any) {
    showAlert("登录失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

function onSmsKeyPress(e: KeyboardEvent) {
  if (e.key === "Enter") doPhoneLogin();
}

function goRegister() {
  router.push("/register");
}

function onKeyPress(e: KeyboardEvent) {
  if (e.key === "Enter") doLogin();
}
</script>

<style scoped>
.login-page {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow-hover);
  border: 1px solid var(--border);
  animation: fadeInUp 0.6s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
.logo-area {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon {
  font-size: 56px;
  margin-bottom: 12px;
}
.logo-title {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.logo-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 6px;
}
.form-group { margin-bottom: 20px; }
.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 14px;
}
.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px;
  transition: all 0.3s;
  font-family: inherit;
  color: var(--text-primary);
  background: #fafbfc;
}
.form-input:focus {
  outline: none;
  border-color: var(--primary-light);
  box-shadow: 0 0 0 4px rgba(33,150,243,0.1);
  background: white;
}
.btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-primary {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
  margin-top: 8px;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(33,150,243,0.35);
}
.btn-secondary {
  background: var(--primary-bg);
  color: var(--primary-dark);
  margin-top: 12px;
}
.btn-secondary:hover { background: #bbdefb; }
.phone-login-section { margin-bottom: 8px; }
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
.btn-phone {
  width: 100%; padding: 14px; border: none; border-radius: var(--radius-sm);
  font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.3s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  background: linear-gradient(135deg, #43a047, #2e7d32); color: white; margin-top: 8px;
}
.btn-phone:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(46,125,50,0.35); }
.alert {
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
  font-size: 14px;
  border-left: 4px solid;
}
.alert-danger { background: #ffebee; color: #c62828; border-color: #ef5350; }
.alert-success { background: #e8f5e9; color: #2e7d32; border-color: #66bb6a; }
.divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
  color: var(--text-muted);
  font-size: 13px;
}
.divider::before, .divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border);
}
.divider span { padding: 0 12px; }
.footer-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: var(--text-muted);
}
.footer-link a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}
.footer-link a:hover { text-decoration: underline; }
</style>
