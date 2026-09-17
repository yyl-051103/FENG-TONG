<template>
<div class="register-page">
<div class="register-card">
<div class="logo-area">
<div class="logo-icon">📝</div>
<div class="logo-title">注册新账号</div>
<div class="logo-subtitle">加入智能风控新闻平台，开启安全内容创作之旅</div>
</div>

<div v-if="alertMsg" :class="['alert', alertType]">{{ alertMsg }}</div>

<form id="registerForm" onsubmit="return false;">
<div class="form-group">
<label class="form-label">账号</label>
<input type="text" class="form-input" v-model="regUsername" placeholder="请输入账号（至少3位）" minlength="3">
</div>
<div class="form-group">
<label class="form-label">密码</label>
<input type="password" class="form-input" v-model="regPassword" placeholder="请输入密码（至少6位）" minlength="6">
</div>
<div class="form-group">
<label class="form-label">昵称</label>
<input type="text" class="form-input" v-model="regNickname" placeholder="请输入昵称（选填）">
</div>
<div class="form-group">
<label class="form-label">手机号</label>
<input type="tel" class="form-input" v-model="regPhone" placeholder="请输入手机号" maxlength="11">
</div>
<div class="form-group sms-row">
<input type="text" class="form-input sms-input" v-model="regSmsCode" placeholder="验证码" maxlength="6">
<button type="button" class="btn-sms" @click="sendRegSms" :disabled="regSmsCountdown > 0">
{{ regSmsCountdown > 0 ? regSmsCountdown + 's后重发' : '获取验证码' }}
</button>
</div>
<div class="form-group" v-if="selectedRole === 'admin'">
<label class="form-label">管理员邀请码</label>
<input type="text" class="form-input" v-model="regInviteCode" placeholder="请输入管理员邀请码" maxlength="10">
</div>
<div class="form-group">
<label class="form-label">选择角色</label>
<div class="role-options">
<div :class="['role-option', { active: selectedRole === 'user' }]" @click="selectRole('user')">
<div class="icon">👤</div>
<div class="label">普通用户</div>
<div class="desc">浏览/发布/互动</div>
</div>
<div :class="['role-option', { active: selectedRole === 'admin' }]" @click="selectRole('admin')">
<div class="icon">🔧</div>
<div class="label">管理员</div>
<div class="desc">发布/审核/管理</div>
</div>
</div>
</div>
<button type="button" class="btn btn-primary" @click="doRegister" :disabled="registering">
<span v-if="registering">⏳</span><span v-else>✅</span> {{ registering ? '注册中...' : '立即注册' }}
</button>
</form>

<div class="divider"><span>或</span></div>

<button type="button" class="btn btn-secondary" @click="goLogin">
<span>🔐</span> 已有账号？去登录
</button>

<div class="footer-link">
已有账号？<router-link to="/login">直接登录</router-link>
</div>
</div>
</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";
import { authApi } from "../api/auth";

const router = useRouter();
const userStore = useUserStore();

const regUsername = ref("");
const regPassword = ref("");
const regNickname = ref("");
const regPhone = ref("");
const regSmsCode = ref("");
const regInviteCode = ref("");
const regSmsCountdown = ref(0);
let regSmsTimer: ReturnType<typeof setInterval> | null = null;
const selectedRole = ref("user");
const registering = ref(false);
const alertMsg = ref("");
const alertType = ref("alert-danger");

function selectRole(role: string) {
  selectedRole.value = role;
}

function showAlert(msg: string, type: string) {
  alertMsg.value = msg;
  alertType.value = "alert-" + type;
  setTimeout(() => { alertMsg.value = ""; }, 4000);
}

async function sendRegSms() {
  const p = regPhone.value.trim();
  if (!p || p.length !== 11) { showAlert("请输入正确的手机号", "danger"); return; }
  try {
    await authApi.sendSms({ phone: p });
    showAlert("验证码已发送", "success");
    regSmsCountdown.value = 60;
    regSmsTimer = setInterval(() => {
      regSmsCountdown.value--;
      if (regSmsCountdown.value <= 0 && regSmsTimer) { clearInterval(regSmsTimer); regSmsTimer = null; }
    }, 1000);
  } catch (err: any) {
    showAlert("发送失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

async function doRegister() {
  const username = regUsername.value.trim();
  const password = regPassword.value.trim();
  const nickname = regNickname.value.trim();
  const phone = regPhone.value.trim();
  const smsCode = regSmsCode.value.trim();

  if (!username) { showAlert("请输入账号", "danger"); return; }
  if (username.length < 3) { showAlert("账号至少3位字符", "danger"); return; }
  if (!password) { showAlert("请输入密码", "danger"); return; }
  if (password.length < 6) { showAlert("密码至少6位字符", "danger"); return; }
  if (!phone || phone.length !== 11) { showAlert("请输入正确的手机号", "danger"); return; }
  if (!smsCode) { showAlert("请输入验证码", "danger"); return; }

  registering.value = true;

  try {
    await userStore.register(username, password, selectedRole.value, nickname || username, phone, smsCode, regInviteCode.value.trim());
    showAlert("注册成功！正在跳转到登录页...", "success");
    setTimeout(() => {
      router.push("/login");
    }, 1500);
  } catch (err: any) {
    showAlert("注册失败：" + (err.response?.data?.detail || err.message), "danger");
    registering.value = false;
  }
}

function goLogin() {
  router.push("/login");
}
</script>

<style scoped>
.register-page {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.register-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 48px 40px;
  width: 100%;
  max-width: 440px;
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
  margin-bottom: 28px;
}
.logo-icon { font-size: 48px; margin-bottom: 8px; }
.logo-title {
  font-size: 22px; font-weight: 800;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.logo-subtitle {
  font-size: 14px; color: var(--text-muted); margin-top: 4px;
}
.form-group { margin-bottom: 18px; }
.form-label {
  display: block; margin-bottom: 6px;
  font-weight: 600; color: var(--text-secondary); font-size: 14px;
}
.form-input, .form-select {
  width: 100%; padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px; transition: all 0.3s;
  font-family: inherit; color: var(--text-primary);
  background: #fafbfc;
}
.form-input:focus, .form-select:focus {
  outline: none; border-color: var(--primary-light);
  box-shadow: 0 0 0 4px rgba(33,150,243,0.1);
  background: white;
}
.role-options {
  display: flex; gap: 12px;
}
.role-option {
  flex: 1;
  padding: 14px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}
.role-option:hover { border-color: var(--primary-light); }
.role-option.active {
  border-color: var(--primary);
  background: var(--primary-bg);
  color: var(--primary-dark);
}
.role-option .icon { font-size: 24px; margin-bottom: 6px; }
.role-option .label { font-size: 14px; font-weight: 600; }
.role-option .desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.btn {
  width: 100%; padding: 14px;
  border: none; border-radius: var(--radius-sm);
  font-size: 16px; font-weight: 700;
  cursor: pointer; transition: all 0.3s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-primary {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; margin-top: 8px;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(33,150,243,0.35);
}
.btn-secondary {
  background: var(--primary-bg); color: var(--primary-dark);
  margin-top: 12px;
}
.btn-secondary:hover { background: #bbdefb; }
.alert {
  padding: 12px 16px; border-radius: var(--radius-sm);
  margin-bottom: 16px;
  font-size: 14px; border-left: 4px solid;
}
.alert-danger { background: #ffebee; color: #c62828; border-color: #ef5350; }
.alert-success { background: #e8f5e9; color: #2e7d32; border-color: #66bb6a; }
.divider {
  display: flex; align-items: center;
  margin: 20px 0; color: var(--text-muted); font-size: 13px;
}
.divider::before, .divider::after {
  content: ""; flex: 1; height: 1px; background: var(--border);
}
.divider span { padding: 0 12px; }
.footer-link {
  text-align: center; margin-top: 20px;
  font-size: 14px; color: var(--text-muted);
}
.footer-link a {
  color: var(--primary); text-decoration: none; font-weight: 600;
}
.footer-link a:hover { text-decoration: underline; }
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
</style>
