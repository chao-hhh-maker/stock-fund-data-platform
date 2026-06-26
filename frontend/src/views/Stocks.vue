<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><TrendCharts /></el-icon><span>股票行情</span></div>
        <div class="page-desc">查询股票日线、K 线走势、成交量和数据来源；管理员可直接触发全量或增量采集。</div>
      </div>
      <div class="page-actions">
        <span v-if="selectedInstrument" class="source-chip real">{{ selectedInstrument.name }} · {{ selectedInstrument.code }}</span>
        <span class="source-chip" :class="auth.canExport ? 'real' : 'sample'">{{ auth.canExport ? '允许导出' : '无导出权限' }}</span>
      </div>
    </div>

    <div class="toolbar-card">
      <el-form :inline="true" class="query-form">
        <el-form-item label="股票">
          <el-select v-model="code" filterable style="width: 240px" @change="onFilterChange">
            <el-option v-for="i in instruments" :key="i.code" :label="`${i.name} (${i.code})`" :value="i.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始" end-placeholder="结束" @change="onFilterChange" />
        </el-form-item>
        <el-form-item label="图表">
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button value="kline">K线</el-radio-button>
            <el-radio-button value="line">收盘线</el-radio-button>
          </el-radio-group>
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
      <div class="metric-tile glass-card"><span class="metric-label">最新收盘</span><span class="metric-value mono-num">{{ latest.close ?? '-' }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">最新涨跌</span><span class="metric-value mono-num" :class="latest.pct_change >= 0 ? 'text-up' : 'text-down'">{{ signed(latest.pct_change) }}%</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">区间最高</span><span class="metric-value mono-num text-up">{{ rangeHigh }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">区间最低</span><span class="metric-value mono-num text-down">{{ rangeLow }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">来源占比</span><span class="metric-value source-mini">{{ sourceSummary }}</span></div>
    </div>

    <el-card v-loading="loading">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><DataLine /></el-icon><span>{{ chartType === 'kline' ? 'K线与成交量' : '收盘价走势' }}</span></div>
          <span class="text-dim small">共 {{ total }} 条记录</span>
        </div>
      </template>
      <KLineChart v-if="chartType === 'kline' && chartRows.length" :rows="chartRows" :height="430" />
      <LineChart v-else-if="chartRows.length" :categories="dates" :series="lineSeries" :height="430" />
      <el-empty v-else description="暂无股票行情数据" :image-size="90" />
    </el-card>

    <el-card v-loading="loading">
      <template #header><div class="section-title"><el-icon><Tickets /></el-icon><span>行情明细</span></div></template>
      <el-table :data="rows" stripe height="360" empty-text="暂无数据">
        <el-table-column prop="trade_date" label="日期" width="120" />
        <el-table-column prop="open" label="开盘" />
        <el-table-column prop="high" label="最高" />
        <el-table-column prop="low" label="最低" />
        <el-table-column prop="close" label="收盘" />
        <el-table-column label="涨跌幅">
          <template #default="{ row }"><span :class="row.pct_change >= 0 ? 'text-up' : 'text-down'" class="mono-num">{{ signed(row.pct_change) }}%</span></template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量" />
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
import { Search, Download, Upload, TrendCharts, DataLine, Tickets } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import LineChart from '../components/LineChart.vue'
import KLineChart from '../components/KLineChart.vue'

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
const chartType = ref('kline')
const mode = ref('full')

const selectedInstrument = computed(() => instruments.value.find((i) => i.code === code.value))
const chartRows = computed(() => [...rows.value].sort((a, b) => String(a.trade_date).localeCompare(String(b.trade_date))))
const dates = computed(() => chartRows.value.map((r) => r.trade_date))
const lineSeries = computed(() => [{ name: '收盘价', data: chartRows.value.map((r) => r.close) }])
const latest = computed(() => chartRows.value[chartRows.value.length - 1] || {})
const rangeHigh = computed(() => rows.value.length ? Math.max(...rows.value.map(r => Number(r.high) || 0)).toFixed(2) : '-')
const rangeLow = computed(() => rows.value.length ? Math.min(...rows.value.map(r => Number(r.low) || 0)).toFixed(2) : '-')
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
  const { data } = await api.instruments({ asset_type: 'stock', page_size: 200 })
  instruments.value = data.items
  if (!code.value && instruments.value.length) code.value = instruments.value[0].code
}
async function load() {
  if (!code.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (dateRange.value?.length === 2) { params.start_date = dateRange.value[0]; params.end_date = dateRange.value[1] }
    const { data } = await api.stockDaily(code.value, params)
    rows.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}
function onFilterChange() { page.value = 1; load() }
function onPage(p) { page.value = p; load() }
async function onCrawl() {
  crawling.value = true
  try {
    const { data } = await api.quickCrawl({ job_type: 'stock_daily', target_codes: code.value, mode: mode.value })
    ElMessage.success(`采集完成：${data.message}`)
    await load()
  } finally { crawling.value = false }
}
async function onExport() {
  exporting.value = true
  try {
    const { data } = await api.createExport({ dataset: 'stock_daily', file_format: 'csv', code: code.value })
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
