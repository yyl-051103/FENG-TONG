<template>
  <div class="page-container">
    <NavBar />

    <div class="toolbar">
      <button class="btn-add" @click="showForm = true; editingId = null; resetForm()">
        + 新增抢购
      </button>
    </div>

    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div>
      <div>加载中...</div>
    </div>

    <div v-else-if="!items.length" class="empty-state">暂无抢购活动</div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>礼品</th>
            <th>积分价</th>
            <th>现金价</th>
            <th>库存</th>
            <th>开始时间</th>
            <th>结束时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.gift_name }}</td>
            <td>{{ item.flash_price_points }}</td>
            <td>¥{{ item.flash_price_cash?.toFixed(2) || "0.00" }}</td>
            <td>{{ item.flash_stock }}</td>
            <td>{{ formatTime(item.start_time) }}</td>
            <td>{{ formatTime(item.end_time) }}</td>
            <td>
              <span :class="['status-tag', item.status]">{{ item.status }}</span>
            </td>
            <td>
              <button class="btn-edit" @click="startEdit(item)">编辑</button>
              <button class="btn-delete" @click="doDelete(item.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 表单弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-box">
        <h3>{{ editingId ? "编辑抢购" : "新增抢购" }}</h3>
        <div class="form-group">
          <label>礼品</label>
          <select v-model="form.gift_id">
            <option :value="0" disabled>请选择礼品</option>
            <option v-for="g in gifts" :key="g.id" :value="g.id">
              {{ g.name }} (库存: {{ g.stock }})
            </option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>抢购积分价</label>
            <input v-model.number="form.flash_price_points" type="number" min="0" />
          </div>
          <div class="form-group">
            <label>抢购现金价</label>
            <input v-model.number="form.flash_price_cash" type="number" min="0" step="0.01" />
          </div>
        </div>
        <div class="form-group">
          <label>抢购库存</label>
          <input v-model.number="form.flash_stock" type="number" min="1" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>开始时间</label>
            <input v-model="form.start_time" type="datetime-local" />
          </div>
          <div class="form-group">
            <label>结束时间</label>
            <input v-model="form.end_time" type="datetime-local" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-save" @click="doSave">保存</button>
          <button class="btn-cancel" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import NavBar from "../../components/NavBar.vue";
import { flashSaleAdminApi, type FlashSaleAdminItem } from "../../api/flash-sale";
import { giftAdminApi, type GiftItem } from "../../api/gift";

const items = ref<FlashSaleAdminItem[]>([]);
const gifts = ref<GiftItem[]>([]);
const loading = ref(true);
const showForm = ref(false);
const editingId = ref<number | null>(null);

const form = ref({
  gift_id: 0,
  flash_price_points: 0,
  flash_price_cash: 0,
  flash_stock: 1,
  start_time: "",
  end_time: "",
});

function resetForm() {
  form.value = {
    gift_id: 0,
    flash_price_points: 0,
    flash_price_cash: 0,
    flash_stock: 1,
    start_time: "",
    end_time: "",
  };
}

function toLocalISO(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

function startEdit(item: FlashSaleAdminItem) {
  editingId.value = item.id;
  form.value = {
    gift_id: item.gift_id,
    flash_price_points: item.flash_price_points,
    flash_price_cash: item.flash_price_cash,
    flash_stock: item.flash_stock,
    start_time: toLocalISO(item.start_time),
    end_time: toLocalISO(item.end_time),
  };
  showForm.value = true;
}

async function loadData() {
  loading.value = true;
  try {
    const [fsRes, giftRes] = await Promise.all([
      flashSaleAdminApi.list(),
      giftAdminApi.list(),
    ]);
    items.value = fsRes.data.data?.items || [];
    gifts.value = giftRes.data.data?.items || [];
  } catch (e: any) {
    const status = e?.response?.status;
    const detail = e?.response?.data?.detail || e?.message || "未知错误";
    console.error("[FlashSaleManage] 加载失败:", status, detail, e);
    if (status === 403) {
      alert("无管理员权限，请确认已登录管理员账号");
    } else if (status === 401) {
      alert("登录已过期，请重新登录");
    } else {
      alert(`加载数据失败: ${detail}`);
    }
  } finally {
    loading.value = false;
  }
}

/** 弹窗打开时，若礼品列表为空则重新加载（兜底） */
watch(showForm, (val) => {
  if (val && gifts.value.length === 0) {
    giftAdminApi.list().then((res) => {
      gifts.value = res.data.data?.items || [];
    }).catch((e: any) => {
      const detail = e?.response?.data?.detail || e?.message || "未知错误";
      console.error("[FlashSaleManage] 礼品列表加载失败:", detail, e);
      alert(`礼品列表加载失败: ${detail}`);
    });
  }
});

async function doSave() {
  if (!form.value.gift_id || !form.value.start_time || !form.value.end_time) {
    alert("请填写完整信息");
    return;
  }
  try {
    if (editingId.value) {
      await flashSaleAdminApi.update(editingId.value, form.value);
    } else {
      await flashSaleAdminApi.create(form.value);
    }
    showForm.value = false;
    await loadData();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "操作失败");
  }
}

async function doDelete(id: number) {
  if (!confirm("确定删除该抢购活动？")) return;
  try {
    await flashSaleAdminApi.delete(id);
    await loadData();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "删除失败");
  }
}

onMounted(loadData);
</script>

<style scoped>
.toolbar {
  margin-bottom: 20px;
}
.btn-add {
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #ff6f00, #e65100);
  color: white;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-add:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(255, 111, 0, 0.4);
}
.table-wrap {
  overflow-x: auto;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px;
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
}
td {
  padding: 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}
.status-tag {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}
.status-tag.进行中 {
  background: #ff6f00;
  color: white;
}
.status-tag.未开始 {
  background: #e3f2fd;
  color: #1565c0;
}
.status-tag.已结束 {
  background: #eee;
  color: #999;
}
.btn-edit,
.btn-delete {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-right: 4px;
}
.btn-edit {
  background: #e3f2fd;
  color: #1565c0;
}
.btn-delete {
  background: #ffebee;
  color: #c62828;
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
  padding: 32px;
  min-width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}
.modal-box h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  box-sizing: border-box;
}
.form-row {
  display: flex;
  gap: 12px;
}
.form-row .form-group {
  flex: 1;
}
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
.btn-save {
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--primary);
  color: white;
  font-weight: 700;
  cursor: pointer;
}
.btn-cancel {
  padding: 10px 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: white;
  cursor: pointer;
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
</style>
