<template>
<div class="page-container">
<NavBar />

<div class="section-header">
  <h2 class="section-title">礼品管理</h2>
  <button class="btn-add" @click="openCreate">+ 新增礼品</button>
</div>

<!-- 加载 / 空状态 -->
<div v-if="loading" class="loading-wrap">
  <div class="spinner"></div><div>加载中...</div>
</div>
<div v-else-if="!gifts.length" class="empty-state">暂无礼品数据</div>

<!-- 表格 -->
<div v-else class="table-wrap">
<table>
  <thead>
    <tr>
      <th>图片</th>
      <th>名称</th>
      <th>分类</th>
      <th>积分</th>
      <th>价格</th>
      <th>库存</th>
      <th>状态</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <tr v-for="g in gifts" :key="g.id">
      <td>
        <img v-if="g.image" :src="g.image" class="gift-thumb" />
        <span v-else class="no-image">-</span>
      </td>
      <td class="gift-name">{{ truncate(g.name, 20) }}</td>
      <td>{{ g.category || '-' }}</td>
      <td>{{ g.points_required }}</td>
      <td>{{ g.price > 0 ? '¥' + g.price : '免费' }}</td>
      <td>{{ g.stock }}</td>
      <td>
        <span :class="['status-badge', g.status === '上架' ? 'status-on' : 'status-off']">
          {{ g.status }}
        </span>
      </td>
      <td class="action-cell">
        <button class="btn btn-edit" @click="openEdit(g)">编辑</button>
        <button class="btn btn-toggle" @click="toggleStatus(g)">
          {{ g.status === '上架' ? '下架' : '上架' }}
        </button>
        <button class="btn btn-del" @click="handleDelete(g.id)">删除</button>
      </td>
    </tr>
  </tbody>
</table>
</div>

<!-- 弹窗表单 -->
<div v-if="showForm" class="modal-overlay" @click.self="closeForm">
  <div class="modal-card">
    <h3 class="modal-title">{{ isEdit ? '编辑礼品' : '新增礼品' }}</h3>
    <form @submit.prevent="submitForm">
      <div class="form-grid">
        <div class="form-field">
          <label>名称</label>
          <input v-model="form.name" required placeholder="礼品名称" />
        </div>
        <div class="form-field">
          <label>分类</label>
          <input v-model="form.category" placeholder="如：限定周边" />
        </div>
        <div class="form-field">
          <label>所需积分</label>
          <input v-model.number="form.points_required" type="number" min="0" required />
        </div>
        <div class="form-field">
          <label>现金价格（元）</label>
          <input v-model.number="form.price" type="number" min="0" step="0.01" required />
        </div>
        <div class="form-field">
          <label>库存</label>
          <input v-model.number="form.stock" type="number" min="0" required />
        </div>
        <div class="form-field">
          <label>状态</label>
          <select v-model="form.status">
            <option value="上架">上架</option>
            <option value="下架">下架</option>
          </select>
        </div>
      </div>
      <div class="form-field form-field-full">
        <label>图片 URL</label>
        <input v-model="form.image" placeholder="https://..." />
      </div>
      <div class="form-field form-field-full">
        <label>描述</label>
        <textarea v-model="form.description" rows="3" placeholder="礼品描述"></textarea>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-cancel" @click="closeForm">取消</button>
        <button type="submit" class="btn btn-save" :disabled="submitting">
          {{ submitting ? '保存中...' : '保存' }}
        </button>
      </div>
    </form>
  </div>
</div>

</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import NavBar from "../../components/NavBar.vue";
import { giftAdminApi, type GiftItem, type GiftForm } from "../../api/gift";

const loading = ref(true);
const gifts = ref<GiftItem[]>([]);

// 弹窗
const showForm = ref(false);
const isEdit = ref(false);
const editingId = ref<number | null>(null);
const submitting = ref(false);

const defaultForm = (): GiftForm => ({
  name: "",
  description: "",
  image: "",
  points_required: 0,
  price: 0,
  stock: 0,
  category: "",
  status: "上架",
});

const form = ref<GiftForm>(defaultForm());

function truncate(text: string, len: number) {
  if (!text) return "";
  return text.length > len ? text.substring(0, len) + "..." : text;
}

async function loadGifts() {
  loading.value = true;
  try {
    const res = await giftAdminApi.list();
    const raw = (res.data as any).data;
    gifts.value = raw?.items || (Array.isArray(raw) ? raw : []);
  } catch (e) {
    console.error("[GiftManage] 加载礼品列表失败:", e);
    gifts.value = [];
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  isEdit.value = false;
  editingId.value = null;
  form.value = defaultForm();
  showForm.value = true;
}

function openEdit(gift: GiftItem) {
  isEdit.value = true;
  editingId.value = gift.id;
  form.value = {
    name: gift.name,
    description: gift.description,
    image: gift.image,
    points_required: gift.points_required,
    price: gift.price,
    stock: gift.stock,
    category: gift.category,
    status: gift.status,
  };
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
}

async function submitForm() {
  submitting.value = true;
  try {
    if (isEdit.value && editingId.value) {
      await giftAdminApi.update(editingId.value, form.value);
    } else {
      await giftAdminApi.create(form.value);
    }
    showForm.value = false;
    await loadGifts();
  } catch {
    alert("操作失败，请重试");
  } finally {
    submitting.value = false;
  }
}

async function toggleStatus(gift: GiftItem) {
  const newStatus = gift.status === "上架" ? "下架" : "上架";
  if (!confirm(`确定将「${gift.name}」设为${newStatus}？`)) return;
  try {
    await giftAdminApi.update(gift.id, {
      name: gift.name,
      description: gift.description,
      image: gift.image,
      points_required: gift.points_required,
      price: gift.price,
      stock: gift.stock,
      category: gift.category,
      status: newStatus,
    });
    await loadGifts();
  } catch {
    alert("操作失败");
  }
}

async function handleDelete(id: number) {
  if (!confirm("确定删除该礼品？不可恢复！")) return;
  try {
    await giftAdminApi.delete(id);
    await loadGifts();
  } catch {
    alert("删除失败");
  }
}

onMounted(() => {
  loadGifts();
});
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.section-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}
.btn-add {
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--primary) 0%, #1565c0 100%);
  color: white;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-add:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.4);
}
.table-wrap {
  overflow-x: auto;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  padding: 24px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th {
  background: var(--primary-bg);
  color: var(--primary-dark);
  padding: 12px;
  text-align: left;
  font-weight: 700;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}
tr:hover td {
  background: var(--primary-bg);
}
.gift-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--border);
}
.no-image {
  display: inline-block;
  width: 48px;
  height: 48px;
  line-height: 48px;
  text-align: center;
  background: var(--primary-bg);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
}
.gift-name {
  font-weight: 600;
  color: var(--text-primary);
}
.status-badge {
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
.status-on {
  background: #e8f5e9;
  color: #2e7d32;
}
.status-off {
  background: #ffebee;
  color: #c62828;
}
.action-cell {
  white-space: nowrap;
}
.btn {
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 4px;
}
.btn-edit {
  background: var(--primary-bg);
  color: var(--primary-dark);
}
.btn-edit:hover {
  background: #bbdefb;
}
.btn-toggle {
  background: #fff8e1;
  color: #f57f17;
}
.btn-toggle:hover {
  background: #ffecb3;
}
.btn-del {
  background: #ffebee;
  color: #c62828;
}
.btn-del:hover {
  background: #ffcdd2;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
  width: 560px;
  max-width: 90vw;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.18);
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 20px;
  color: var(--text-primary);
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.form-field input,
.form-field select,
.form-field textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--surface);
  transition: border-color 0.2s;
}
.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: var(--primary);
}
.form-field-full {
  grid-column: 1 / -1;
  margin-bottom: 16px;
}
textarea {
  resize: vertical;
  font-family: inherit;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.btn-cancel {
  background: var(--primary-bg);
  color: var(--text-secondary);
}
.btn-cancel:hover {
  background: #e0e0e0;
}
.btn-save {
  background: linear-gradient(135deg, var(--primary) 0%, #1565c0 100%);
  color: white;
}
.btn-save:hover {
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
}
.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.loading-wrap {
  text-align: center;
  padding: 40px;
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
  padding: 60px 20px;
  color: var(--text-muted);
  font-size: 14px;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
</style>
