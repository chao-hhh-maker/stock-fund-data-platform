<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Money /></el-icon><span>基金净值</span></div>
        <div class="page-desc">查询基金单位净值、累计净值和区间收益；管理员可触发基金净值采集。</div>
      </div>
      <div class="page-actions">
        <span v-if="selectedInstrument" class="source-chip real">{{ selectedInstrument.name }} · {{ selectedInstrument.code }}</span>
        <span class="source-chip" :class="auth.canExport ? 'real' : 'sample'">{{ auth.canExport ? '允许导出' : '无导出权限' }}</span>
      </div>
    </div>

    <div class="toolbar-card">
      <el-form :inline="true" class="query-form">
        <el-form-item label="基金">
          <el-select v-model="code" filterable style="width: 240px" @change="onFilterChange">
            <el-option v-for="i in instruments" :key="i.code" :label="`${i.name} (${i.code})`" :value="i.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始" end-placeholder="结束" @change="onFilterChange" />
        </el-form-item>
        <el-form-item class="actions-item">
          <el-button type="primary" :icon="Search" :loading="loading" @click="load">查询</el-button>
          <template v-if="auth.isAdmin">
            <el-select v-model="mode" style="width: 104px">
              <el-option label="全量" value="full" />
              <el-option label="增量" value="incremental" />
            </el-select>
            <el-button type="success" :icon="Upload" @click="onCrawl" :loading="crawling">采集</el-button>
          </template>
          <el-button v-if="auth.canExport" :icon="Download" @click="onExport" :loading="exporting">导出</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="metric-grid" v-if="rows.length">
      <div class="metric-tile glass-card"><span class="metric-label">最新单位净值</span><span class="metric-value mono-num text-accent">{{ latest.unit_nav ?? '-' }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">最新累计净值</span><span class="metric-value mono-num">{{ latest.accum_nav ?? '-' }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">最新日增长</span><span class="metric-value mono-num" :class="latest.daily_return >= 0 ? 'text-up' : 'text-down'">{{ signed(latest.daily_return) }}%</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">区间累计涨幅</span><span class="metric-value mono-num" :class="cumReturn >= 0 ? 'text-up' : 'text-down'">{{ signed(cumReturn) }}%</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">来源占比</span><span class="metric-value source-mini">{{ sourceSummary }}</span></div>
    </div>

    <el-card v-loading="loading">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><DataLine /></el-icon><span>单位净值 / 累计净值走势</span></div>
          <span class="text-dim small">共 {{ total }} 条记录</span>
        </div>
      </template>
      <LineChart v-if="chartRows.length" :categories="dates" :series="chartSeries" :height="420" />
      <el-empty v-else description="暂无基金净值数据" :image-size="90" />
    </el-card>

    <el-card v-loading="loading">
      <template #header><div class="section-title"><el-icon><Tickets /></el-icon><span>净值明细</span></div></template>
      <el-table :data="rows" stripe height="360" empty-text="暂无数据">
        <el-table-column prop="nav_date" label="日期" width="120" />
        <el-table-column prop="unit_nav" label="单位净值" />
        <el-table-column prop="accum_nav" label="累计净值" />
        <el-table-column label="日增长率">
          <template #default="{ row }"><span :class="row.daily_return >= 0 ? 'text-up' : 'text-down'" class="mono-num">{{ signed(row.daily_return) }}%</span></template>
        </el-table-column>
        <el-table-column label="来源" width="120">
          <template #default="{ row }"><span class="source-chip" :class="sourceClass(row.source)">{{ row.source || '-' }}</span></template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next" :total="total" :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, Upload, Money, DataLine, Tickets } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import LineChart from '../components/LineChart.vue'

const auth = useAuthStore()
const instruments = ref([])
const code = ref('')
const dateRange = ref([])
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 500
const loading = ref(false)
const crawling = ref(false)
const exporting = ref(false)
const mode = ref('full')

const selectedInstrument = computed(() => instruments.value.find((i) => i.code === code.value))
const chartRows = computed(() => [...rows.value].sort((a, b) => String(a.nav_date).localeCompare(String(b.nav_date))))
const dates = computed(() => chartRows.value.map((r) => r.nav_date))
const chartSeries = computed(() => [
  { name: '单位净值', data: chartRows.value.map((r) => r.unit_nav) },
  { name: '累计净值', data: chartRows.value.map((r) => r.accum_nav) },
])
const latest = computed(() => chartRows.value[chartRows.value.length - 1] || {})
const cumReturn = computed(() => {
  if (chartRows.value.length < 2) return 0
  const first = Number(chartRows.value[0].unit_nav || 0)
  const last = Number(chartRows.value[chartRows.value.length - 1].unit_nav || 0)
  return first ? Number(((last - first) / first * 100).toFixed(2)) : 0
})
const sourceSummary = computed(() => {
  if (!rows.value.length) return '-'
  const real = rows.value.filter((r) => r.source !== 'sample').length
  return `${real}/${rows.value.length} 真实源`
})

function signed(v) {
  const n = Number(v || 0)
  return `${n >= 0 ? '+' : ''}${n}`
}
function sourceClass(source = '') { return source.includes('sample') ? 'sample' : source ? 'real' : '' }
async function loadInstruments() {
  const { data } = await api.instruments({ asset_type: 'fund', page_size: 200 })
  instruments.value = data.items
  if (!code.value && instruments.value.length) code.value = instruments.value[0].code
}
async function load() {
  if (!code.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (dateRange.value?.length === 2) { params.start_date = dateRange.value[0]; params.end_date = dateRange.value[1] }
    const { data } = await api.fundNav(code.value, params)
    rows.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}
function onFilterChange() { page.value = 1; load() }
function onPage(p) { page.value = p; load() }
async function onCrawl() {
  crawling.value = true
  try {
    const { data } = await api.quickCrawl({ job_type: 'fund_nav', target_codes: code.value, mode: mode.value })
    ElMessage.success(`采集完成：${data.message}`)
    await load()
  } finally { crawling.value = false }
}
async function onExport() {
  exporting.value = true
  try {
    const { data } = await api.createExport({ dataset: 'fund_nav', file_format: 'csv', code: code.value })
    ElMessage.success(`已导出 ${data.row_count} 行，可在数据导出页下载`)
  } finally { exporting.value = false }
}
onMounted(async () => { await loadInstruments(); await load() })
</script>

<style scoped>
.query-form { display: flex; align-items: center; flex-wrap: wrap; gap: 2px 8px; }
.actions-item :deep(.el-form-item__content) { gap: 8px; }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.small { font-size: 12px; }
.source-mini { font-size: 16px; color: var(--accent); }
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
