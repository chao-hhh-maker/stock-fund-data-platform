<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title">
          <el-icon><DataBoard /></el-icon>
          <span>数据驾驶舱</span>
        </div>
        <div class="page-desc">集中展示标的规模、行情数据量、实时快照、采集成功率和最近任务运行状态。</div>
      </div>
      <div class="page-actions">
        <div class="status-line">
          <span class="status-dot" :class="wsOn ? 'ok' : 'warn'"></span>
          {{ wsOn ? 'WebSocket 推送' : 'HTTP 轮询' }}
        </div>
        <el-button :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <div class="ticker-wrap" v-if="ticks.length">
      <div class="ticker-state">
        <span class="status-dot" :class="marketOpen ? 'ok' : 'warn'"></span>
        <span>{{ marketOpen ? (realtime ? '实时行情' : '盘中快照') : '最新收盘' }}</span>
      </div>
      <div class="ticker">
        <div class="ticker-item" v-for="t in ticks" :key="t.code">
          <span class="t-name">{{ t.name }}</span>
          <span class="t-price mono-num">{{ t.price }}</span>
          <span class="t-chg mono-num" :class="t.pct_change >= 0 ? 'up' : 'down'">
            {{ t.pct_change >= 0 ? '+' : '' }}{{ t.pct_change }}%
          </span>
        </div>
      </div>
      <span class="ticker-ts text-dim mono-num">{{ wsTs }}</span>
    </div>

    <div class="cards">
      <StatCard label="股票标的" :value="stats.stock_count" color="#35d0ba" :icon="TrendCharts" sub="已纳入管理" bar-width="65%" />
      <StatCard label="基金标的" :value="stats.fund_count" color="#7aa2f7" :icon="Money" sub="已纳入管理" bar-width="45%" />
      <StatCard label="股票日线" :value="stats.stock_daily_rows" color="#20c997" :icon="DataLine" sub="累计入库行数" bar-width="82%" />
      <StatCard label="基金净值" :value="stats.fund_nav_rows" color="#f2b84b" :icon="Coin" sub="累计入库行数" bar-width="62%" />
    </div>

    <el-row :gutter="16" class="row">
      <el-col :span="16">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-head">
              <div class="section-title"><el-icon><TrendCharts /></el-icon><span>标的走势速览</span></div>
              <el-select v-model="quickCode" size="small" style="width: 240px" filterable @change="loadTrend">
                <el-option v-for="i in stockList" :key="i.code" :label="`${i.name} (${i.code})`" :value="i.code" />
              </el-select>
            </div>
          </template>
          <LineChart v-if="trendDates.length" :categories="trendDates" :series="trendSeries" :height="320" />
          <el-empty v-else description="暂无走势数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card v-loading="loading">
          <template #header><div class="section-title"><el-icon><CircleCheck /></el-icon><span>采集成功率</span></div></template>
          <MiniChart type="gauge" :value="stats.crawl_success_rate" title="运行成功率" :height="205" />
          <div class="gauge-foot">
            <span class="text-sub">任务总数</span>
            <span class="mono-num text-accent">{{ stats.job_count }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="row">
      <el-col :span="8">
        <el-card v-loading="loading">
          <template #header><div class="section-title"><el-icon><Histogram /></el-icon><span>行业 / 类型分布</span></div></template>
          <MiniChart type="pie" :data="stats.industry_distribution" :height="300" />
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-head">
              <div class="section-title"><el-icon><Operation /></el-icon><span>最近采集运行</span></div>
              <span class="text-dim small">展示最近 6 条运行记录</span>
            </div>
          </template>
          <el-table :data="stats.recent_runs" size="small" :show-header="true" empty-text="暂无采集记录">
            <el-table-column prop="id" label="ID" width="56" />
            <el-table-column label="触发" width="82">
              <template #default="{ row }">
                <el-tag size="small" effect="plain" :type="row.trigger === 'manual' ? 'warning' : 'info'">
                  {{ row.trigger === 'manual' ? '手动' : '定时' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="88">
              <template #default="{ row }">
                <el-tag size="small" effect="dark" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="rows_affected" label="行数" width="86" />
            <el-table-column prop="retries" label="重试" width="68" />
            <el-table-column label="来源" width="150">
              <template #default="{ row }">
                <span class="source-chip" :class="sourceClass(row.source)">{{ row.source || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" :formatter="fmtTime" min-width="150" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import api, { openQuotesWs } from '../api'
import { useAuthStore } from '../stores/auth'
import StatCard from '../components/StatCard.vue'
import LineChart from '../components/LineChart.vue'
import MiniChart from '../components/MiniChart.vue'
import { DataBoard, TrendCharts, Money, DataLine, Coin, CircleCheck, Histogram, Operation, Refresh } from '@element-plus/icons-vue'

const auth = useAuthStore()
const loading = ref(false)
const stats = reactive({
  stock_count: 0, fund_count: 0, stock_daily_rows: 0, fund_nav_rows: 0,
  job_count: 0, crawl_success_rate: 100, industry_distribution: [],
  recent_runs: [], recent_exports: [],
})
const stockList = ref([])
const quickCode = ref('')
const trendDates = ref([])
const trendSeries = ref([])
const ticks = ref([])
const wsTs = ref('')
const wsOn = ref(false)
const marketOpen = ref(false)
const realtime = ref(false)
let ws = null
let pollTimer = null

function applySnap(data) {
  ticks.value = data.quotes || []
  wsTs.value = (data.ts || '').replace('T', ' ')
  marketOpen.value = !!data.market_open
  realtime.value = !!data.realtime
}

function startWs() {
  try {
    ws = openQuotesWs(auth.token)
    ws.onopen = () => { wsOn.value = true; stopPoll() }
    ws.onmessage = (e) => { applySnap(JSON.parse(e.data)) }
    ws.onclose = () => { wsOn.value = false; startPoll() }
    ws.onerror = () => { wsOn.value = false; startPoll() }
  } catch (e) { startPoll() }
}
function startPoll() {
  if (pollTimer) return
  const tick = async () => {
    try { applySnap((await api.realtimeQuotes()).data) } catch (e) { /* ignore */ }
  }
  tick()
  pollTimer = setInterval(tick, 5000)
}
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }
function statusType(s) { return { success: 'success', partial: 'warning', failed: 'danger', running: 'info' }[s] || 'info' }
function statusText(s) { return { success: '成功', partial: '部分', failed: '失败', running: '运行中' }[s] || s }
function fmtTime(row, col, val) { return val ? val.replace('T', ' ').slice(5, 19) : '-' }
function sourceClass(source = '') { return source.includes('sample') ? 'sample' : source ? 'real' : '' }

async function loadTrend() {
  if (!quickCode.value) return
  const { data } = await api.stockDaily(quickCode.value, { page_size: 120 })
  const rows = [...data.items].sort((a, b) => String(a.trade_date).localeCompare(String(b.trade_date)))
  trendDates.value = rows.map((r) => r.trade_date)
  trendSeries.value = [{ name: '收盘价', data: rows.map((r) => r.close) }]
}

async function loadAll() {
  loading.value = true
  try {
    const { data } = await api.dashboard()
    Object.assign(stats, data)
    const inst = await api.instruments({ asset_type: 'stock', page_size: 50 })
    stockList.value = inst.data.items
    if (!quickCode.value && stockList.value.length) quickCode.value = stockList.value[0].code
    await loadTrend()
  } finally {
    loading.value = false
  }
}

onMounted(async () => { await loadAll(); startWs() })
onBeforeUnmount(() => { if (ws) { try { ws.close() } catch (e) {} } stopPoll() })
</script>

<style scoped>
.cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.row { margin-top: 0; }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.small { font-size: 12px; }
.gauge-foot { display: flex; justify-content: space-between; padding: 0 20px 8px; }
.gauge-foot .mono-num { font-size: 20px; font-weight: 740; }
.ticker-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(19, 24, 32, 0.76);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 10px 14px;
  overflow: hidden;
}
.ticker-state { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-sub); white-space: nowrap; }
.ticker { display: flex; gap: 24px; flex: 1; overflow-x: auto; scrollbar-width: none; }
.ticker::-webkit-scrollbar { display: none; }
.ticker-item { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
.t-name { color: var(--text-sub); font-size: 13px; }
.t-price { color: var(--text-main); font-size: 13px; }
.t-chg { font-size: 12px; font-weight: 700; }
.t-chg.up { color: var(--up); }
.t-chg.down { color: var(--down); }
.ticker-ts { font-size: 11px; white-space: nowrap; }
@media (max-width: 720px) { .ticker-ts { display: none; } }
</style>
