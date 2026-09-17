<template>
  <div class="map-page">
    <NavBar />

    <div class="map-body">
      <div class="map-main">
        <!-- 面包屑导航 -->
        <div class="breadcrumb" v-if="drillStack.length">
          <span class="breadcrumb-item" @click="drillBack(0)">全国</span>
          <template v-for="(item, idx) in drillStack" :key="item.adcode">
            <span class="breadcrumb-sep">›</span>
            <span
              class="breadcrumb-item"
              :class="{ active: idx === drillStack.length - 1 }"
              @click="drillBack(idx + 1)"
            >{{ item.name }}</span>
          </template>
        </div>

        <div v-if="mapLoading" class="loading-wrap">
          <div class="spinner"></div>
          <div>正在加载地图数据...</div>
        </div>
        <div ref="chartRef" class="chart" v-show="!mapLoading"></div>
      </div>

      <div class="region-panel">
        <div class="panel-header">
          <h3>{{ panelTitle }}</h3>
          <button v-if="selectedRegion" class="close-btn" @click="clearSelection">✕</button>
        </div>

        <!-- 默认：子级统计列表 -->
        <div v-if="!selectedRegion" class="region-stats-list">
          <div v-if="!childStats.length && !statsLoading" class="empty-tip">暂无数据</div>
          <div v-if="statsLoading" class="loading-inline"><div class="spinner"></div></div>
          <div
            v-for="s in childStats"
            :key="s.name"
            class="region-stat-item"
            @click="onStatClick(s.name)"
          >
            <span class="rs-name">{{ s.name }}</span>
            <span class="rs-count">{{ s.value }} 条</span>
          </div>
        </div>

        <!-- 选中区域后：新闻列表 -->
        <template v-else>
          <div v-if="regionLoading" class="loading-inline">
            <div class="spinner"></div>
          </div>
          <div v-else-if="!regionNews.length" class="empty-tip">暂无新闻</div>
          <div v-else class="region-news-list">
            <div
              v-for="n in regionNews"
              :key="n.id"
              class="region-news-item"
              @click="goDetail(n.id)"
            >
              <div class="rn-title">{{ n.title }}</div>
              <div class="rn-time">{{ formatTime(n.create_time) }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 新闻详情弹窗 -->
    <div v-if="modalVisible" class="modal-overlay" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>新闻详情</h3>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="modalLoading" class="loading-inline"><div class="spinner"></div></div>
          <template v-else-if="modalNews">
            <h4 class="modal-news-title">{{ modalNews.title }}</h4>
            <div class="modal-meta">
              <span v-if="modalNews.source">来源：{{ modalNews.source }}</span>
              <span v-if="modalNews.location">地点：{{ modalNews.location }}</span>
              <span v-if="modalNews.create_time">时间：{{ formatTime(modalNews.create_time) }}</span>
            </div>
            <div class="modal-content" v-html="modalNews.content || '暂无内容'"></div>
            <button class="modal-detail-btn" @click="goDetail(modalNews.id)">查看完整新闻 →</button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import NavBar from "../components/NavBar.vue";
import { mapApi } from "../api/map";
import { newsApi } from "../api/news";

const router = useRouter();
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

/* ---------- 省市区级联数据 ---------- */
interface ProvinceNode { n: string; a: string; c: CityNode[] }
interface CityNode { n: string; a: string; d: string[] }
const regionData = ref<ProvinceNode[]>([]);

/* ---------- 下钻状态 ---------- */
const drillStack = ref<{ name: string; adcode: string }[]>([]);
const mapLoading = ref(true);
const selectedRegion = ref("");
const regionLoading = ref(false);
const regionNews = ref<any[]>([]);
const childStats = ref<{ name: string; value: number }[]>([]);
const statsLoading = ref(false);

/* ---------- 新闻标记点 ---------- */
interface NewsMarker { id: number; title: string; location: string; lat: number | null; lng: number | null }
const markers = ref<NewsMarker[]>([]);

/* ---------- 新闻详情弹窗 ---------- */
const modalVisible = ref(false);
const modalLoading = ref(false);
const modalNews = ref<any>(null);

const currentLevel = computed((): "province" | "city" | "district" => {
  if (drillStack.value.length === 0) return "province";
  if (drillStack.value.length === 1) return "city";
  return "district";
});

const panelTitle = computed(() => {
  if (selectedRegion.value) return selectedRegion.value;
  if (drillStack.value.length === 0) return "全国新闻分布";
  const top = drillStack.value[drillStack.value.length - 1].name;
  return `${top} ${currentLevel.value === "city" ? "各市" : "各区"}统计`;
});

/* ---------- GeoJSON 加载 ---------- */
function getGeoJsonUrl(adcode: string): string {
  return `/api/map/geojson/${adcode}`;
}

const loadedMaps = new Map<string, any>();

async function loadGeoJson(adcode: string): Promise<any> {
  if (loadedMaps.has(adcode)) return loadedMaps.get(adcode);
  const resp = await fetch(getGeoJsonUrl(adcode));
  const json = await resp.json();
  loadedMaps.set(adcode, json);
  return json;
}

/* ---------- 子级统计加载 ---------- */
async function loadChildStats() {
  statsLoading.value = true;
  childStats.value = [];
  try {
    if (drillStack.value.length === 0) {
      const res = await mapApi.regionStats();
      console.log("[MapView] /region-stats 返回数据:", res.data);
      childStats.value = res.data || [];
    } else if (drillStack.value.length === 1) {
      const res = await mapApi.childrenStats("city", drillStack.value[0].name);
      console.log("[MapView] /children-stats (city) 返回数据:", res.data);
      childStats.value = res.data || [];
    } else if (drillStack.value.length === 2) {
      const res = await mapApi.childrenStats("district", drillStack.value[1].name);
      console.log("[MapView] /children-stats (district) 返回数据:", res.data);
      childStats.value = res.data || [];
    }
  } catch (e) {
    console.error("[MapView] 统计接口请求失败:", e);
    childStats.value = [];
  } finally {
    statsLoading.value = false;
  }
}

/* ---------- 标记点加载 ---------- */
async function loadMarkers() {
  try {
    const res = await mapApi.newsMarkers();
    console.log("[MapView] /news-markers 返回数据:", res.data);
    markers.value = (res.data || []).filter((m: NewsMarker) => m.lat != null && m.lng != null);
    console.log("[MapView] 有效标记点数:", markers.value.length, markers.value);
  } catch (e) {
    console.error("[MapView] /news-markers 请求失败:", e);
    markers.value = [];
  }
}

/* ---------- 弹窗 ---------- */
async function openMarkerModal(newsId: number) {
  modalVisible.value = true;
  modalLoading.value = true;
  modalNews.value = null;
  try {
    const res = await newsApi.detail(newsId);
    modalNews.value = res.data;
  } catch {
    modalNews.value = null;
  } finally {
    modalLoading.value = false;
  }
}

function closeModal() {
  modalVisible.value = false;
  modalNews.value = null;
}

/* ---------- 全国地图渲染 ---------- */
async function renderNationMap() {
  mapLoading.value = true;
  try {
    const geoJson = await loadGeoJson("100000");
    echarts.registerMap("china", geoJson);

    let statsData: { name: string; value: number }[] = [];
    try {
      const res = await mapApi.regionStats();
      statsData = res.data || [];
      console.log("[MapView] renderNationMap regionStats:", statsData);
    } catch (e) {
      console.error("[MapView] renderNationMap regionStats 失败:", e);
    }

    mapLoading.value = false;
    await nextTick();
    await new Promise((r) => requestAnimationFrame(r));

    if (chartInstance) chartInstance.dispose();
    chartInstance = echarts.init(chartRef.value!);

    const scatterData = markers.value.map((m) => ({
      name: m.title,
      value: [m.lng!, m.lat!, m.id],
    }));
    console.log("[MapView] scatterData:", scatterData.length, "个标记点");
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          if (params.seriesType === "scatter" || params.seriesType === "effectScatter") {
            return `<b>${params.name}</b><br/>点击查看详情`;
          }
          return params.value > 0
            ? `${params.name}<br/>新闻数: ${params.value}`
            : `${params.name}<br/>暂无新闻`;
        },
      },
      visualMap: {
        min: 0,
        max: 10,
        left: 20,
        bottom: 20,
        text: ["高", "低"],
        inRange: { color: ["#e3f2fd", "#bbdefb", "#64b5f6", "#1e88e5", "#0d47a1"] },
        calculable: false,
      },
      series: [
        {
          type: "scatter",
          coordinateSystem: "geo",
          geoIndex: 0,
          zlevel: 2,
          symbol: "circle",
          symbolSize: 12,
          itemStyle: { color: "#e74c3c", borderColor: "#fff", borderWidth: 2 },
          emphasis: { scale: 1.5 },
          data: scatterData,
        },
        {
          type: "map",
          map: "china",
          geoIndex: 0,
          aspectScale: 0.85,
          emphasis: { label: { show: true, fontSize: 14 }, itemStyle: { areaColor: "#ffd54f" } },
          label: { show: false },
          data: statsData,
        },
      ],
      geo: {
        map: "china",
        roam: true,
        center: [105, 34],
        zoom: 1.2,
        aspectScale: 0.85,
        label: { show: false },
        itemStyle: { areaColor: "#fafafa", borderColor: "#ccc" },
        emphasis: { label: { show: false } },
      },
    };

    chartInstance.setOption(option);
    chartInstance.on("click", onMapClick);
  } catch {
    mapLoading.value = false;
  }
}

/* ---------- 下钻逻辑 ---------- */
async function drillDown(name: string, adcode: string) {
  mapLoading.value = true;
  try {
    const geoJson = await loadGeoJson(adcode);
    const mapName = `map_${adcode}`;
    echarts.registerMap(mapName, geoJson);

    const prevLevel = drillStack.value.length;
    drillStack.value.push({ name, adcode });
    mapLoading.value = false;
    await nextTick();
    await new Promise((r) => requestAnimationFrame(r));

    if (chartInstance) chartInstance.dispose();
    chartInstance = echarts.init(chartRef.value!);

    let mapData: { name: string; value: number }[] = [];
    try {
      if (prevLevel === 0) {
        const res = await mapApi.childrenStats("city", name);
        mapData = res.data || [];
      } else if (prevLevel === 1) {
        const res = await mapApi.childrenStats("district", name);
        mapData = res.data || [];
      }
    } catch (e) {
      console.error("[MapView] drillDown childrenStats 失败:", e);
    }
    childStats.value = mapData;

    const scatterData = markers.value.map((m) => ({
      name: m.title,
      value: [m.lng!, m.lat!, m.id],
    }));
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          if (params.seriesType === "scatter" || params.seriesType === "effectScatter") {
            return `<b>${params.name}</b><br/>点击查看详情`;
          }
          return params.value > 0
            ? `${params.name}<br/>新闻数: ${params.value}`
            : `${params.name}<br/>暂无新闻`;
        },
      },
      visualMap: {
        min: 0,
        max: 10,
        left: 20,
        bottom: 20,
        text: ["高", "低"],
        inRange: { color: ["#e3f2fd", "#bbdefb", "#64b5f6", "#1e88e5", "#0d47a1"] },
        calculable: false,
      },
      series: [
        {
          type: "scatter",
          coordinateSystem: "geo",
          geoIndex: 0,
          zlevel: 2,
          symbol: "circle",
          symbolSize: 12,
          itemStyle: { color: "#e74c3c", borderColor: "#fff", borderWidth: 2 },
          emphasis: { scale: 1.5 },
          data: scatterData,
        },
        {
          type: "map",
          map: mapName,
          geoIndex: 0,
          emphasis: { label: { show: true, fontSize: 14 }, itemStyle: { areaColor: "#ffd54f" } },
          label: { show: false },
          data: mapData,
        },
      ],
      geo: {
        map: mapName,
        roam: true,
        label: { show: false },
        itemStyle: { areaColor: "#fafafa", borderColor: "#ccc" },
        emphasis: { label: { show: false } },
      },
    };

    chartInstance.setOption(option);
    chartInstance.on("click", onMapClick);
  } finally {
    mapLoading.value = false;
    loadChildStats();
  }
}

async function drillBack(level: number) {
  if (level >= drillStack.value.length) return;
  selectedRegion.value = "";
  regionNews.value = [];

  if (level === 0) {
    drillStack.value = [];
    await renderNationMap();
    loadChildStats();
    return;
  }

  drillStack.value = drillStack.value.slice(0, level);
  const target = drillStack.value[drillStack.value.length - 1];
  mapLoading.value = true;
  try {
    const geoJson = await loadGeoJson(target.adcode);
    const mapName = `map_${target.adcode}`;
    echarts.registerMap(mapName, geoJson);
    mapLoading.value = false;
    await nextTick();
    await new Promise((r) => requestAnimationFrame(r));
    if (chartInstance) chartInstance.dispose();
    chartInstance = echarts.init(chartRef.value!);

    let mapData: { name: string; value: number }[] = [];
    try {
      if (drillStack.value.length === 1) {
        const res = await mapApi.childrenStats("city", target.name);
        mapData = res.data || [];
      } else if (drillStack.value.length === 2) {
        const res = await mapApi.childrenStats("district", target.name);
        mapData = res.data || [];
      }
    } catch {}

    const scatterData = markers.value.map((m) => ({
      name: m.title,
      value: [m.lng!, m.lat!, m.id],
    }));
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          if (params.seriesType === "scatter" || params.seriesType === "effectScatter") {
            return `<b>${params.name}</b><br/>点击查看详情`;
          }
          return params.value > 0
            ? `${params.name}<br/>新闻数: ${params.value}`
            : `${params.name}<br/>暂无新闻`;
        },
      },
      visualMap: {
        min: 0,
        max: 10,
        left: 20,
        bottom: 20,
        text: ["高", "低"],
        inRange: { color: ["#e3f2fd", "#bbdefb", "#64b5f6", "#1e88e5", "#0d47a1"] },
        calculable: false,
      },
      series: [
        {
          type: "scatter",
          coordinateSystem: "geo",
          geoIndex: 0,
          zlevel: 2,
          symbol: "circle",
          symbolSize: 12,
          itemStyle: { color: "#e74c3c", borderColor: "#fff", borderWidth: 2 },
          emphasis: { scale: 1.5 },
          data: scatterData,
        },
        {
          type: "map",
          map: mapName,
          geoIndex: 0,
          emphasis: { label: { show: true, fontSize: 14 }, itemStyle: { areaColor: "#ffd54f" } },
          label: { show: false },
          data: mapData,
        },
      ],
      geo: {
        map: mapName,
        roam: true,
        label: { show: false },
        itemStyle: { areaColor: "#fafafa", borderColor: "#ccc" },
        emphasis: { label: { show: false } },
      },
    };
    chartInstance.setOption(option);
    chartInstance.on("click", onMapClick);
  } finally {
    mapLoading.value = false;
    loadChildStats();
  }
}

/* ---------- 地图点击处理 ---------- */
const regionAdcodeMap: Record<string, string> = {};

async function buildAdcodeMap() {
  for (const p of regionData.value) {
    regionAdcodeMap[p.n] = p.a;
    for (const c of p.c) {
      regionAdcodeMap[c.n] = c.a;
    }
  }
}

function getAdcodeByName(name: string): string {
  if (regionAdcodeMap[name]) return regionAdcodeMap[name];
  for (const p of regionData.value) {
    if (name.includes(p.n) || p.n.includes(name)) return p.a;
    for (const c of p.c) {
      if (name.includes(c.n) || c.n.includes(name)) return c.a;
    }
  }
  return "";
}

function onMapClick(params: any) {
  // scatter/effectScatter 标记点点击 → 弹窗
  if (params.seriesType === "scatter" || params.seriesType === "effectScatter") {
    const newsId = params.value?.[2];
    if (newsId) {
      openMarkerModal(newsId);
      return;
    }
  }

  // 地图区域点击 → 下钻或展示新闻
  if (!params.name) return;
  const adcode = getAdcodeByName(params.name);
  if (!adcode) {
    selectRegion(params.name);
    return;
  }
  if (drillStack.value.length >= 2) {
    selectRegion(params.name);
    return;
  }
  drillDown(params.name, adcode);
}

/* ---------- 选择地区显示新闻 ---------- */
function selectRegion(name: string) {
  selectedRegion.value = name;
  loadRegionNews(name);
}

function onStatClick(name: string) {
  const adcode = getAdcodeByName(name);
  if (adcode && drillStack.value.length < 2) {
    drillDown(name, adcode);
  } else {
    selectRegion(name);
  }
}

function clearSelection() {
  selectedRegion.value = "";
  regionNews.value = [];
}

async function loadRegionNews(region: string) {
  regionLoading.value = true;
  regionNews.value = [];
  try {
    const res = await mapApi.regionNews(region);
    regionNews.value = res.data || [];
  } catch {
    regionNews.value = [];
  } finally {
    regionLoading.value = false;
  }
}

/* ---------- 工具函数 ---------- */
function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function goDetail(id: number) {
  router.push(`/news/${id}`);
}

function handleResize() {
  chartInstance?.resize();
}

async function loadRegionData() {
  try {
    const resp = await fetch("/china-regions.json");
    regionData.value = await resp.json();
    await buildAdcodeMap();
  } catch {}
}

/* ---------- 初始化 ---------- */
onMounted(async () => {
  await loadRegionData();
  await loadMarkers();
  await renderNationMap();
  loadChildStats();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chartInstance?.dispose();
});
</script>

<style scoped>
.map-page {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}

.map-body {
  flex: 1;
  display: flex;
  gap: 24px;
  padding: 0 32px 32px;
  max-width: 100%;
  box-sizing: border-box;
}

.map-main {
  flex: 1;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  position: relative;
  min-height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.chart {
  flex: 1;
  width: 100%;
  min-height: 0;
}

/* 面包屑 */
.breadcrumb {
  position: absolute;
  top: 12px;
  left: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  border-radius: 8px;
  padding: 6px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-size: 13px;
}
.breadcrumb-item {
  color: var(--primary);
  cursor: pointer;
  font-weight: 500;
  transition: color 0.2s;
}
.breadcrumb-item:hover {
  color: var(--primary-dark);
  text-decoration: underline;
}
.breadcrumb-item.active {
  color: var(--text-primary);
  font-weight: 700;
  cursor: default;
  text-decoration: none;
}
.breadcrumb-sep {
  color: var(--text-muted);
  user-select: none;
}

.loading-wrap {
  text-align: center;
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

.region-panel {
  width: 320px;
  flex-shrink: 0;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  max-height: calc(100vh - 180px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(135deg, var(--primary-bg), var(--surface));
  flex-shrink: 0;
}
.panel-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary-dark);
}
.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-muted);
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}
.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

.loading-inline {
  text-align: center;
  padding: 40px;
}
.empty-tip {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 14px;
}

.region-stats-list {
  overflow-y: auto;
  flex: 1;
  padding: 4px;
}
.region-stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border);
}
.region-stat-item:last-child {
  border-bottom: none;
}
.region-stat-item:hover {
  background: var(--primary-bg);
}
.rs-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.rs-count {
  font-size: 13px;
  color: var(--primary);
  font-weight: 600;
}

.region-news-list {
  overflow-y: auto;
  flex: 1;
  padding: 8px;
}
.region-news-item {
  padding: 12px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border);
}
.region-news-item:last-child {
  border-bottom: none;
}
.region-news-item:hover {
  background: var(--primary-bg);
}
.rn-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.rn-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* ── 新闻详情弹窗 ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-card {
  background: var(--surface);
  border-radius: 12px;
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.modal-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--primary-dark);
}
.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px 8px;
  border-radius: 4px;
}
.modal-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}
.modal-news-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.5;
}
.modal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.modal-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
}
.modal-content :deep(img) {
  max-width: 100%;
}
.modal-detail-btn {
  display: inline-block;
  padding: 8px 20px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.modal-detail-btn:hover {
  background: var(--primary-dark);
}

@media (max-width: 1000px) {
  .map-body {
    flex-direction: column;
    padding: 0 16px 16px;
  }
  .region-panel {
    width: 100%;
    max-height: 300px;
  }
  .modal-card {
    width: 95vw;
  }
}
</style>
