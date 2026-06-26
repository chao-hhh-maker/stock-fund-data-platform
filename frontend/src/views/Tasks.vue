<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Operation /></el-icon><span>采集任务</span></div>
        <div class="page-desc">管理定时采集任务，支持手动执行、一键全量采集、运行记录和日志追踪。</div>
      </div>
      <div class="page-actions" v-if="auth.isAdmin">
        <el-dropdown @command="onCrawlAll" trigger="click">
          <el-button type="warning" :loading="crawlingAll">
            一键采集 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="all">全部标的（股票+基金）</el-dropdown-item>
              <el-dropdown-item command="stock">仅股票</el-dropdown-item>
              <el-dropdown-item command="fund">仅基金</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建任务</el-button>
      </div>
    </div>

    <div class="metric-grid task-summary">
      <div class="metric-tile glass-card"><span class="metric-label">任务总数</span><span class="metric-value mono-num">{{ jobs.length }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">启用任务</span><span class="metric-value mono-num text-down">{{ enabledCount }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">最近运行</span><span class="metric-value task-status">{{ latestRunText }}</span></div>
    </div>

    <el-card v-loading="loadingJobs">
      <template #header><div class="section-title"><el-icon><Setting /></el-icon><span>任务配置</span></div></template>
      <el-table :data="jobs" stripe empty-text="暂无任务">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="job_type" label="类型" width="120"><template #default="{ row }">{{ jobTypeText(row.job_type) }}</template></el-table-column>
        <el-table-column prop="target_codes" label="目标代码" min-width="170" show-overflow-tooltip />
        <el-table-column label="模式" width="82"><template #default="{ row }"><el-tag size="small" effect="plain" :type="row.mode === 'incremental' ? 'success' : 'info'">{{ row.mode === 'incremental' ? '增量' : '全量' }}</el-tag></template></el-table-column>
        <el-table-column label="频率" width="92"><template #default="{ row }"><el-tag size="small" effect="plain">{{ freqText(row.frequency) }}</el-tag></template></el-table-column>
        <el-table-column prop="cron" label="定时(cron)" width="150"><template #default="{ row }">{{ row.cron || '手动' }}</template></el-table-column>
        <el-table-column prop="enabled" label="启用" width="82"><template #default="{ row }"><el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '是' : '否' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="245">
          <template #default="{ row }">
            <el-button size="small" @click="viewLogs(row)">日志</el-button>
            <template v-if="auth.isAdmin">
              <el-button size="small" type="success" @click="runJob(row)" :loading="runningId === row.id">执行</el-button>
              <el-button size="small" type="danger" @click="removeJob(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-loading="loadingRuns">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><Clock /></el-icon><span>最近运行记录</span></div>
          <el-button size="small" text :icon="Refresh" @click="loadRuns">刷新</el-button>
        </div>
      </template>
      <el-table :data="runs" size="small" empty-text="暂无运行记录">
        <el-table-column prop="id" label="ID" width="56" />
        <el-table-column prop="job_id" label="任务" width="64" />
        <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag size="small" effect="dark" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="rows_affected" label="行数" width="80" />
        <el-table-column prop="retries" label="重试" width="64" />
        <el-table-column label="来源" width="150"><template #default="{ row }"><span class="source-chip" :class="sourceClass(row.source)">{{ row.source || '-' }}</span></template></el-table-column>
        <el-table-column prop="message" label="信息" show-overflow-tooltip />
        <el-table-column prop="started_at" label="开始" width="160" :formatter="fmtTime" />
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" title="新建采集任务" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="任务名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.job_type"><el-option label="股票日线" value="stock_daily" /><el-option label="基金净值" value="fund_nav" /><el-option label="公告/舆情" value="announcement" /></el-select></el-form-item>
        <el-form-item label="目标代码"><el-input v-model="form.target_codes" placeholder="逗号分隔，如 600519.SH,000001.SZ" /></el-form-item>
        <el-form-item label="采集模式"><el-radio-group v-model="form.mode"><el-radio value="full">全量</el-radio><el-radio value="incremental">增量</el-radio></el-radio-group></el-form-item>
        <el-form-item label="更新频率"><el-select v-model="form.frequency" @change="onFreqChange"><el-option label="实时(每分钟)" value="realtime" /><el-option label="分钟级(每5分钟)" value="minute" /><el-option label="日级(收盘后)" value="daily" /><el-option label="周级" value="weekly" /><el-option label="季度" value="quarterly" /><el-option label="仅手动" value="manual" /></el-select><span class="freq-hint">频率自动映射 cron</span></el-form-item>
        <el-form-item label="定时cron"><el-input v-model="form.cron" placeholder="留空则按频率自动生成，如 0 18 * * 1-5" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="submit">创建</el-button></template>
    </el-dialog>

    <el-drawer v-model="logDrawer" title="运行日志" size="50%">
      <el-table :data="logs" size="small" empty-text="暂无运行记录">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="trigger" label="触发" width="80" />
        <el-table-column prop="status" label="状态" width="90"><template #default="{ row }"><el-tag size="small" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="rows_affected" label="行数" width="70" />
        <el-table-column prop="retries" label="重试" width="60" />
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="message" label="信息" show-overflow-tooltip />
        <el-table-column prop="started_at" label="开始" :formatter="fmtTime" />
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Refresh, Operation, Plus, Setting, Clock } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const jobs = ref([])
const runs = ref([])
const dialog = ref(false)
const logDrawer = ref(false)
const logs = ref([])
const runningId = ref(null)
const crawlingAll = ref(false)
const loadingJobs = ref(false)
const loadingRuns = ref(false)
let refreshTimer = null
const form = reactive({ name: '', job_type: 'stock_daily', target_codes: '', mode: 'full', frequency: 'daily', cron: '' })
const enabledCount = computed(() => jobs.value.filter((j) => j.enabled).length)
const latestRunText = computed(() => runs.value[0] ? statusText(runs.value[0].status) : '暂无')

function jobTypeText(t) { return { stock_daily: '股票日线', fund_nav: '基金净值', announcement: '公告/舆情' }[t] || t }
function freqText(f) { return { realtime: '实时', minute: '分钟级', daily: '日级', weekly: '周级', quarterly: '季度', manual: '手动' }[f] || (f || '日级') }
function onFreqChange() { form.cron = '' }
function statusType(s) { return { success: 'success', partial: 'warning', failed: 'danger', running: 'info' }[s] || 'info' }
function statusText(s) { return { success: '成功', partial: '部分', failed: '失败', running: '运行中' }[s] || s }
function sourceClass(source = '') { return source.includes('sample') ? 'sample' : source ? 'real' : '' }
function fmtTime(row, col, val) { return val ? val.replace('T', ' ').slice(0, 19) : '-' }
async function loadRuns() { loadingRuns.value = true; try { const { data } = await api.listRuns({ page: 1, page_size: 15 }); runs.value = data.items } finally { loadingRuns.value = false } }
async function onCrawlAll(assetType) {
  crawlingAll.value = true
  try {
    const { data } = await api.crawlAll({ asset_type: assetType, mode: 'full' })
    ElMessage.success(data.message || '采集任务已提交后台执行')
    let ticks = 0
    refreshTimer && clearInterval(refreshTimer)
    refreshTimer = setInterval(() => { loadRuns(); load(); if (++ticks >= 15) { clearInterval(refreshTimer); refreshTimer = null } }, 2000)
  } finally { crawlingAll.value = false }
}
async function load() { loadingJobs.value = true; try { const { data } = await api.listJobs(); jobs.value = data } finally { loadingJobs.value = false } }
function openCreate() { Object.assign(form, { name: '', job_type: 'stock_daily', target_codes: '', mode: 'full', frequency: 'daily', cron: '' }); dialog.value = true }
async function submit() { await api.createJob({ ...form }); ElMessage.success('任务已创建'); dialog.value = false; load() }
async function runJob(row) { runningId.value = row.id; try { const { data } = await api.runJob(row.id); ElMessage.success(`执行完成：${data.status}，影响 ${data.rows_affected} 行（来源 ${data.source}）`); loadRuns() } finally { runningId.value = null } }
async function removeJob(row) { await ElMessageBox.confirm(`确认删除任务「${row.name}」？`, '提示', { type: 'warning' }); await api.deleteJob(row.id); ElMessage.success('已删除'); load() }
async function viewLogs(row) { const { data } = await api.jobLogs(row.id, { limit: 50 }); logs.value = data; logDrawer.value = true }
onMounted(() => { load(); loadRuns() })
onBeforeUnmount(() => { refreshTimer && clearInterval(refreshTimer) })
</script>

<style scoped>
.task-summary { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.task-status { font-size: 19px; color: var(--accent); }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.freq-hint { font-size: 11px; color: var(--text-dim); margin-left: 8px; }
</style>
