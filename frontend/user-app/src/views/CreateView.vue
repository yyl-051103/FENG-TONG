<template>
<div class="page-container">
<NavBar />

<div class="main-grid">
<div class="card">
<div class="card-title"><span>📝</span> 新闻创作</div>
<div v-if="alertMsg" :class="['alert', alertType]" v-html="alertMsg"></div>
<form id="newsForm" onsubmit="return false;">
<div class="form-group">
<label class="form-label">新闻标题</label>
<input type="text" class="form-input" v-model="titleInput" placeholder="请输入新闻标题（1-255字）" maxlength="255">
</div>
<div class="form-group">
<label class="form-label">新闻内容</label>
<Editor
  tinymce-script-src="https://cdn.tiny.cloud/1/ijjxl69duke1s614ii80h5wqowhr0ma1i9713ax14ewln1vd/tinymce/6/tinymce.min.js"
  :init="tinymceConfig"
  v-model="contentValue"
/>
</div>
<div class="form-group">
<label class="form-label">新闻来源</label>
<input type="text" class="form-input" v-model="sourceInput" placeholder="如：XX新闻网（选填）" maxlength="100">
</div>
<div class="form-group">
<label class="form-label">新闻地点</label>
<div class="region-selects">
  <div class="custom-select region-select" :class="{ disabled: false }">
    <div class="custom-select-trigger" @click="toggleProvince">
      <span :class="{ placeholder: !selProvince }">{{ provinceLabel || '-- 请选择省 --' }}</span>
      <span class="arrow">▾</span>
    </div>
    <div class="custom-select-dropdown" v-show="showProvince">
      <div class="custom-select-options">
        <div class="custom-select-option" @click="selectProvince('')">-- 请选择省 --</div>
        <div v-for="p in provinces" :key="p.a" class="custom-select-option" :class="{ selected: selProvince === p.a }" @click="selectProvince(p.a)">{{ p.n }}</div>
      </div>
    </div>
  </div>
  <div class="custom-select region-select" :class="{ disabled: !selProvince }">
    <div class="custom-select-trigger" @click="toggleCity">
      <span :class="{ placeholder: !selCity }">{{ cityLabel || '-- 请选择市 --' }}</span>
      <span class="arrow">▾</span>
    </div>
    <div class="custom-select-dropdown" v-show="showCity && selProvince">
      <div class="custom-select-options">
        <div class="custom-select-option" @click="selectCity('')">-- 请选择市 --</div>
        <div v-for="c in cities" :key="c.a" class="custom-select-option" :class="{ selected: selCity === c.a }" @click="selectCity(c.a)">{{ c.n }}</div>
      </div>
    </div>
  </div>
  <div class="custom-select region-select" :class="{ disabled: !selCity }">
    <div class="custom-select-trigger" @click="toggleDistrict">
      <span :class="{ placeholder: !selDistrict }">{{ selDistrict || '-- 请选择区 --' }}</span>
      <span class="arrow">▾</span>
    </div>
    <div class="custom-select-dropdown" v-show="showDistrict && selCity">
      <div class="custom-select-options">
        <div class="custom-select-option" @click="selectDistrict('')">-- 请选择区 --</div>
        <div v-for="d in districts" :key="d" class="custom-select-option" :class="{ selected: selDistrict === d }" @click="selectDistrict(d)">{{ d }}</div>
      </div>
    </div>
  </div>
</div>
</div>
<div class="btn-group">
<button type="button" class="btn btn-primary" @click="publishNews">
<span>🚀</span> 发布新闻
</button>
<button type="button" class="btn btn-secondary" @click="clearForm">
<span>🔄</span> 清空
</button>
</div>
</form>
</div>

<div class="info-panel">
<div class="card">
<div class="card-title"><span>📊</span> 发布统计</div>
<div style="font-size: 14px; color: var(--text-secondary); line-height: 2;">
<p>✅ 已通过：<strong>{{ countPass }}</strong> 篇</p>
<p>⏳ 待审核：<strong>{{ countPending }}</strong> 篇</p>
<p>❌ 已拒绝：<strong>{{ countReject }}</strong> 篇</p>
</div>
</div>
<div class="card">
<div class="card-title"><span>📋</span> 我的发布</div>
<div id="myNewsList" style="max-height: 320px; overflow-y: auto;">
<p v-if="!myNews.length" style="color: var(--text-muted); font-size: 14px; text-align: center; padding: 20px;">暂无发布记录</p>
<div v-for="n in myNews" :key="n.id" class="news-item">
<router-link :to="'/news/' + n.id" class="news-item-title">{{ n.title }}</router-link>
<div class="news-item-meta">
<span :class="['status-badge', n.status==='已通过'?'status-pass':n.status==='待审核'?'status-pending':'status-reject']">{{ n.status }}</span>
<span>{{ formatTime(n.create_time) }}</span>
</div>
<div v-if="n.risk_reason" style="font-size:12px; color:#c62828; margin-top:4px;">{{ n.risk_reason }}</div>
<div style="margin-top:6px;">
<button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" @click="deleteNews(n.id)">删除</button>
</div>
</div>
</div>
</div>
</div>
</div>

<div class="ai-float">
<div :class="['ai-panel', { show: aiPanelOpen }]">
<div class="ai-header">
<span>🤖 AI创作助手</span>
<button class="ai-close" @click="toggleAI">×</button>
</div>
<div class="ai-body" @click="handleAiAction">
<div class="ai-tabs">
<div :class="['ai-tab', { active: aiTab === 'optimize' }]" @click="aiTab = 'optimize'">内容优化</div>
<div :class="['ai-tab', { active: aiTab === 'format' }]" @click="aiTab = 'format'">格式调整</div>
<div :class="['ai-tab', { active: aiTab === 'inspire' }]" @click="aiTab = 'inspire'">灵感生成</div>
<div :class="['ai-tab', { active: aiTab === 'history' }]" @click="aiTab = 'history'; loadHistory()">历史记录</div>
</div>
<div v-show="aiTab === 'optimize'">
<textarea class="ai-input" v-model="optimizeInput" placeholder="粘贴您的新闻草稿，AI将优化语病、表达和逻辑..."></textarea>
<button class="btn btn-primary" style="width: 100%;" @click="doAssist('优化')">
<span>✨</span> AI优化内容
</button>
<div id="optimizeResult" v-html="aiResults.optimize"></div>
</div>
<div v-show="aiTab === 'format'">
<textarea class="ai-input" v-model="formatInput" placeholder="粘贴内容，AI将自动分段、规范标题层级和标点..."></textarea>
<button class="btn btn-primary" style="width: 100%;" @click="doAssist('格式调整')">
<span>📐</span> AI调整格式
</button>
<div id="formatResult" v-html="aiResults.format"></div>
</div>
<div v-show="aiTab === 'inspire'">
<input type="text" class="ai-input" v-model="inspireInput" placeholder="输入关键词，如：科技新闻、环保动态..." style="min-height: 40px;">
<button class="btn btn-primary" style="width: 100%;" @click="doAssist('灵感生成')">
<span>💡</span> AI生成灵感
</button>
<div id="inspireResult" v-html="aiResults.inspire"></div>
</div>
<div v-show="aiTab === 'history'">
<div v-if="!aiRecords.length" style="color: var(--text-muted); font-size: 14px; text-align: center; padding: 20px;">暂无历史记录</div>
<div v-for="r in aiRecords" :key="r.id" class="history-item">
<div class="history-type">{{ r.assist_type }}</div>
<div class="history-time">{{ formatTime(r.create_time) }}</div>
<div class="history-content">{{ truncate(r.optimized_content, 80) }}...</div>
<div class="history-actions">
<button class="btn btn-success" @click="reuseRecord(r.id)">复用</button>
<button class="btn btn-danger" @click="deleteRecord(r.id)">删除</button>
</div>
</div>
<button class="btn btn-secondary" style="width: 100%; margin-top: 10px;" @click="loadHistory">
<span>🔄</span> 刷新记录
</button>
</div>
</div>
</div>
<button class="ai-float-btn" @click="toggleAI">🤖</button>
</div>
</div>
</template>

<script setup lang="ts">
/* UI polish v2 - ai-result-box */
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue";
import NavBar from "../components/NavBar.vue";
import { newsApi } from "../api/news";
import Editor from "@tinymce/tinymce-vue";

/* ---------- 地址级联数据 ---------- */
interface ProvinceNode { n: string; a: string; c: CityNode[] }
interface CityNode { n: string; a: string; d: string[] }

const regionData = ref<ProvinceNode[]>([]);
const provinces = ref<ProvinceNode[]>([]);
const cities = ref<CityNode[]>([]);
const districts = ref<string[]>([]);
const selProvince = ref("");
const selCity = ref("");
const selDistrict = ref("");

const titleInput = ref("");
const sourceInput = ref("");
const alertMsg = ref("");
const alertType = ref("");
const countPass = ref(0);
const countPending = ref(0);
const countReject = ref(0);
const myNews = ref<any[]>([]);
const aiPanelOpen = ref(false);
const aiTab = ref("optimize");
const optimizeInput = ref("");
const formatInput = ref("");
const inspireInput = ref("");
const aiResults = reactive({ optimize: "", format: "", inspire: "" });
const aiRecords = ref<any[]>([]);

// TinyMCE 富文本编辑器配置
const contentValue = ref("");
const tinymceConfig = {
  height: 300,
  menubar: false,
  plugins: "advlist lists fontfamily fontsize align lineheight textcolor",
  toolbar: "fontfamily fontsize bold italic underline alignleft aligncenter alignright lineheight forecolor backcolor",
  language: "zh_CN",
  content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto; font-size: 15px; line-height: 1.7; }',
  placeholder: "请输入新闻正文内容...",
  skin: "oxide",
};

/* ---------- 级联逻辑 ---------- */
const showProvince = ref(false);
const showCity = ref(false);
const showDistrict = ref(false);

function findProvince(adcode: string): ProvinceNode | undefined {
  return regionData.value.find((p) => p.a === adcode);
}
function findCity(adcode: string): CityNode | undefined {
  for (const p of regionData.value) {
    const c = p.c.find((c) => c.a === adcode);
    if (c) return c;
  }
  return undefined;
}

const provinceLabel = computed(() => {
  const p = findProvince(selProvince.value);
  return p ? p.n : "";
});
const cityLabel = computed(() => {
  const c = findCity(selCity.value);
  return c ? c.n : "";
});

function closeAllDropdowns() {
  showProvince.value = false;
  showCity.value = false;
  showDistrict.value = false;
}

function toggleProvince() {
  showProvince.value = !showProvince.value;
  showCity.value = false;
  showDistrict.value = false;
}
function toggleCity() {
  if (!selProvince.value) return;
  showCity.value = !showCity.value;
  showProvince.value = false;
  showDistrict.value = false;
}
function toggleDistrict() {
  if (!selCity.value) return;
  showDistrict.value = !showDistrict.value;
  showProvince.value = false;
  showCity.value = false;
}

function selectProvince(adcode: string) {
  if (adcode === "") {
    selProvince.value = "";
    selCity.value = "";
    selDistrict.value = "";
    cities.value = [];
    districts.value = [];
  } else {
    selProvince.value = adcode;
    selCity.value = "";
    selDistrict.value = "";
    districts.value = [];
    const p = findProvince(adcode);
    cities.value = p ? p.c : [];
  }
  showProvince.value = false;
}
function selectCity(adcode: string) {
  if (adcode === "") {
    selCity.value = "";
    selDistrict.value = "";
    districts.value = [];
  } else {
    selCity.value = adcode;
    selDistrict.value = "";
    const c = findCity(adcode);
    districts.value = c ? c.d : [];
  }
  showCity.value = false;
}
function selectDistrict(name: string) {
  selDistrict.value = name === "" ? "" : name;
  showDistrict.value = false;
}

function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (!target.closest(".custom-select")) {
    closeAllDropdowns();
  }
}

function getLocationString(): string {
  let loc = "";
  const p = findProvince(selProvince.value);
  if (p) loc += p.n;
  const c = findCity(selCity.value);
  if (c && c.n !== loc) loc += c.n;
  if (selDistrict.value && selDistrict.value !== loc) loc += selDistrict.value;
  return loc || "";
}

async function loadRegionData() {
  try {
    const resp = await fetch("/china-regions.json");
    regionData.value = await resp.json();
    provinces.value = regionData.value;
  } catch {
    // 静默失败，不影响其他功能
  }
}

/* ---------- 原有逻辑 ---------- */
function showAlert(msg: string, type: string, duration = 6000) {
  alertMsg.value = msg;
  alertType.value = "alert-" + type;
  if (duration > 0) {
    setTimeout(() => { alertMsg.value = ""; }, duration);
  }
}

function toggleAI() {
  aiPanelOpen.value = !aiPanelOpen.value;
}

const aiResultTexts: Record<string, string> = {};

function escapeHtml(text: string) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

function handleAiAction(e: Event) {
  const btn = (e.target as HTMLElement).closest("button") as HTMLButtonElement | null;
  if (!btn) return;
  const aiKey = btn.dataset.aiKey;
  if (!aiKey) return;
  const text = aiResultTexts[aiKey] || "";
  if (btn.dataset.action === "copy") {
    navigator.clipboard.writeText(text).then(() => showAlert("已复制到剪贴板", "success"));
  } else {
    contentValue.value = text.replace(/\n/g, "<br>");
    showAlert("内容已填充到编辑器", "success");
    toggleAI();
  }
}

function truncate(text: string, len: number) {
  return text ? text.substring(0, len) : "";
}

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

async function doAssist(type: string) {
  let content = "";
  if (type === "优化") content = optimizeInput.value.trim();
  else if (type === "格式调整") content = formatInput.value.trim();
  else content = inspireInput.value.trim();

  if (!content) { showAlert("请输入内容后再使用AI辅助", "warning"); return; }

  const key = type === "优化" ? "optimize" : type === "格式调整" ? "format" : "inspire";
  aiResults[key] = '<div class="spinner-text"><div class="loading"></div> AI正在处理中...</div>';

  try {
    const title = titleInput.value.trim() || "未设置标题";
    const assistType = type === "优化" ? "内容优化" : type;
    const res = await newsApi.aiAssist({ original_content: content, assist_type: assistType, title });
    const optimized = res.data.optimized_content;
    aiResultTexts[key] = optimized;
    aiResults[key] = `
      <div class="ai-result-box">
        <div class="ai-result">${escapeHtml(optimized)}</div>
        <div class="ai-actions">
          <button class="btn btn-ai-apply" data-ai-key="${key}"><span>✅</span> 应用到表单</button>
          <button class="btn btn-ai-copy" data-ai-key="${key}" data-action="copy"><span>📋</span> 复制</button>
        </div>
      </div>
    `;
    showAlert("AI辅助完成，请查看结果", "success");
    loadHistory();
  } catch (err: any) {
    aiResults[key] = `<div style="color:#c62828;font-size:14px;">请求失败：${err.message}</div>`;
    showAlert("AI辅助请求失败", "danger");
  }
}

async function publishNews() {
  const title = titleInput.value.trim();
  const content = contentValue.value;
  const source = sourceInput.value.trim();
  const location = getLocationString();

  if (!title) { showAlert("请输入新闻标题", "warning"); return; }
  if (!content) { showAlert("请输入新闻内容", "warning"); return; }

  showAlert("正在提交并启动AI风控审核，请稍候...", "info", 0);
  try {
    const res = await newsApi.publish({ title, content, source, location: location || undefined });
    const data = res.data;
    if (data.status === "已通过") {
      showAlert(`✅ ${data.msg}（风险等级：${data.risk_level}）`, "success");
      clearForm();
    } else {
      showAlert(`❌ ${data.msg}（风险等级：${data.risk_level}）`, "danger");
    }
    loadMyNews();
  } catch (err: any) {
    showAlert("发布失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

function clearForm() {
  titleInput.value = "";
  sourceInput.value = "";
  selProvince.value = "";
  selCity.value = "";
  selDistrict.value = "";
  cities.value = [];
  districts.value = [];
  contentValue.value = "";
  alertMsg.value = "";
}

async function loadMyNews() {
  try {
    const res = await newsApi.my();
    const news: any[] = res.data || [];
    let pass = 0, pending = 0, reject = 0;
    news.forEach((n: any) => {
      if (n.status === "已通过") pass++;
      else if (n.status === "待审核") pending++;
      else if (n.status === "已拒绝") reject++;
    });
    countPass.value = pass;
    countPending.value = pending;
    countReject.value = reject;
    myNews.value = news;
  } catch {}
}

async function deleteNews(id: number) {
  if (!confirm("确定删除这条新闻吗？删除后不可恢复。")) return;
  try {
    await newsApi.delete(id);
    loadMyNews();
    showAlert("删除成功", "success");
  } catch (err: any) {
    showAlert("删除失败：" + (err.response?.data?.detail || err.message), "danger");
  }
}

async function loadHistory() {
  try {
    const res = await newsApi.aiRecords();
    aiRecords.value = res.data || [];
  } catch {
    aiRecords.value = [];
  }
}

async function reuseRecord(id: number) {
  try {
    const res = await newsApi.aiRecords();
    const record = (res.data || []).find((r: any) => r.id === id);
    if (record) {
      contentValue.value = record.optimized_content.replace(/\n/g, "<br>");
      showAlert("历史记录已复用到编辑器", "success");
      toggleAI();
    }
  } catch { showAlert("复用失败", "danger"); }
}

async function deleteRecord(id: number) {
  if (!confirm("确定删除这条记录吗？")) return;
  try {
    await newsApi.deleteAiRecord(id);
    loadHistory();
    showAlert("删除成功", "success");
  } catch { showAlert("删除失败", "danger"); }
}

onMounted(() => {
  loadRegionData();
  loadMyNews();
  loadHistory();
  document.addEventListener("click", onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocumentClick);
});
</script>

<style scoped>

.main-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
}
.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.card-title {
  font-size: 20px; font-weight: 700;
  margin-bottom: 20px; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px;
}
.form-group { margin-bottom: 20px; }
.form-label {
  display: block; margin-bottom: 8px;
  font-weight: 600; color: var(--text-secondary); font-size: 14px;
}
.form-input {
  width: 100%; padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px; transition: all 0.3s;
  font-family: inherit; color: var(--text-primary);
  background: #fafbfc;
}
.form-input:focus {
  outline: none; border-color: var(--primary-light);
  box-shadow: 0 0 0 4px rgba(33,150,243,0.1);
  background: white;
}
.region-selects {
  display: flex;
  gap: 12px;
}

.custom-select {
  position: relative;
  flex: 1;
  min-width: 0;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 14px;
  background: #fafbfc;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  cursor: pointer;
  user-select: none;
  transition: border-color 0.3s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.custom-select-trigger .placeholder {
  color: var(--text-secondary);
}

.custom-select-trigger .arrow {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 8px;
  flex-shrink: 0;
}

.custom-select.disabled .custom-select-trigger {
  background: var(--bg-disabled, #f0f2f5);
  color: #bbb;
  cursor: not-allowed;
  border-color: var(--border);
}

.custom-select-dropdown {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}

.custom-select-options {
  max-height: 212px;
  overflow-y: auto;
  padding: 4px 0;
}

.custom-select-option {
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s;
}

.custom-select-option:hover {
  background: var(--primary-bg, #e3f2fd);
}

.custom-select-option.selected {
  color: var(--primary, #2196F3);
  background: var(--primary-bg, #e3f2fd);
  font-weight: 600;
}
.tox-tinymce {
  border: 2px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  overflow: hidden;
}
.tox-tinymce:focus-within {
  border-color: var(--primary-light) !important;
}
.btn {
  padding: 12px 24px; border: none; border-radius: var(--radius-sm);
  font-size: 15px; font-weight: 600; cursor: pointer;
  transition: all 0.3s; display: inline-flex;
  align-items: center; gap: 8px;
}
.btn-primary {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(33,150,243,0.35);
}
.btn-secondary {
  background: var(--primary-bg); color: var(--primary-dark);
}
.btn-secondary:hover { background: #bbdefb; }
.btn-danger {
  background: #ffebee; color: #c62828;
}
.btn-danger:hover { background: #ffcdd2; }
.btn-success {
  background: #e8f5e9; color: #2e7d32;
}
.btn-success:hover { background: #c8e6c9; }
.btn-group { display: flex; gap: 12px; margin-top: 20px; }
.alert {
  padding: 14px 18px; border-radius: var(--radius-sm);
  margin-bottom: 20px;
  animation: slideIn 0.4s ease; font-size: 14px;
  border-left: 4px solid;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.alert-success { background: #e8f5e9; color: #2e7d32; border-color: #66bb6a; }
.alert-danger { background: #ffebee; color: #c62828; border-color: #ef5350; }
.alert-warning { background: #fff8e1; color: #f57f17; border-color: #ffca28; }
.alert-info { background: #e3f2fd; color: #1565c0; border-color: var(--primary-light); }
.info-panel { display: flex; flex-direction: column; gap: 20px; }
.status-badge {
  display: inline-block; padding: 4px 12px;
  border-radius: 20px; font-size: 12px; font-weight: 700;
}
.status-pass { background: #e8f5e9; color: #2e7d32; }
.status-pending { background: #fff8e1; color: #f57f17; }
.status-reject { background: #ffebee; color: #c62828; }
.news-item {
  padding: 12px; border-bottom: 1px solid var(--border);
  transition: all 0.2s; border-radius: var(--radius-sm);
}
.news-item:hover { background: var(--primary-bg); }
.news-item:last-child { border-bottom: none; }
.news-item-title {
  font-weight: 600; color: var(--primary-dark);
  font-size: 14px; margin-bottom: 4px;
  cursor: pointer; text-decoration: none;
}
.news-item-title:hover { text-decoration: underline; }
.news-item-meta {
  font-size: 12px; color: var(--text-muted);
  display: flex; justify-content: space-between; align-items: center;
}
.ai-float { position: fixed; bottom: 30px; right: 30px; z-index: 1000; }
.ai-float-btn {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; border: none; font-size: 22px;
  cursor: pointer; box-shadow: var(--shadow-hover);
  transition: all 0.3s; display: flex;
  align-items: center; justify-content: center;
}
.ai-float-btn:hover { transform: scale(1.1); }
.ai-panel {
  position: absolute; bottom: 70px; right: 0;
  width: 400px; max-height: 540px;
  background: var(--surface); border-radius: var(--radius);
  box-shadow: var(--shadow-hover); display: none;
  flex-direction: column; overflow: hidden;
  animation: popUp 0.3s ease; border: 1px solid var(--border);
}
@keyframes popUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.ai-panel.show { display: flex; }
.ai-header {
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  color: white; padding: 16px 20px;
  font-weight: 700; display: flex;
  justify-content: space-between; align-items: center;
}
.ai-close { background: none; border: none; color: white; font-size: 20px; cursor: pointer; }
.ai-body { padding: 16px; overflow-y: auto; flex: 1; }
.ai-tabs { display: flex; gap: 6px; margin-bottom: 16px; }
.ai-tab {
  flex: 1; padding: 8px; border: 2px solid var(--border);
  border-radius: var(--radius-sm); background: white;
  cursor: pointer; font-size: 13px; font-weight: 600;
  text-align: center; transition: all 0.3s; color: var(--text-secondary);
}
.ai-tab.active {
  border-color: var(--primary); background: var(--primary);
  color: white;
}
.ai-tab:hover:not(.active) { border-color: var(--primary-light); color: var(--primary); }
.ai-input {
  width: 100%; padding: 10px; border: 2px solid var(--border);
  border-radius: var(--radius-sm); margin-bottom: 12px;
  font-size: 14px; resize: vertical; min-height: 80px;
  font-family: inherit; color: var(--text-primary);
}
.ai-input:focus { outline: none; border-color: var(--primary-light); }
.ai-result-box {
  border: 2px solid var(--border); border-radius: 12px;
  background: var(--primary-bg); padding: 14px;
  margin-top: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.ai-result {
  background: white; border: 1px solid #e8e8e8;
  border-radius: 8px; padding: 14px;
  font-size: 14px; line-height: 1.7;
  max-height: 200px; overflow-y: auto; white-space: pre-wrap;
  color: var(--text-primary);
}
.ai-actions { display: flex; gap: 10px; margin-top: 12px; }
.ai-actions .btn { flex: 1; padding: 10px 14px; font-size: 14px; font-weight: 600; border-radius: 8px; justify-content: center; transition: all 0.2s; }
.btn-ai-apply { background: linear-gradient(135deg, #43a047, #66bb6a); color: white; border: none; }
.btn-ai-apply:hover { background: linear-gradient(135deg, #2e7d32, #43a047); transform: translateY(-1px); box-shadow: 0 3px 8px rgba(46,125,50,0.3); }
.btn-ai-copy { background: linear-gradient(135deg, #546e7a, #78909c); color: white; border: none; }
.btn-ai-copy:hover { background: linear-gradient(135deg, #37474f, #546e7a); transform: translateY(-1px); box-shadow: 0 3px 8px rgba(55,71,79,0.3); }
.history-item {
  background: var(--primary-bg); border-radius: var(--radius-sm);
  padding: 12px; margin-bottom: 10px;
  border-left: 4px solid var(--primary-light);
}
.history-type { font-size: 12px; color: var(--primary-dark); font-weight: 700; margin-bottom: 4px; }
.history-time { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
.history-content { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.history-actions { display: flex; gap: 6px; margin-top: 8px; }
.history-actions .btn { padding: 4px 10px; font-size: 12px; }
.loading { display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3); border-radius: 50%;
  border-top-color: white; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.spinner-text {
  display: flex; align-items: center; gap: 8px;
  color: var(--primary); font-size: 14px; margin: 12px 0;
}
@media (max-width: 900px) {
  .main-grid { grid-template-columns: 1fr; }
  .ai-panel { width: calc(100vw - 40px); right: -10px; }
}
</style>
