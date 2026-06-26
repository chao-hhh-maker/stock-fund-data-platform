<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Monitor /></el-icon><span>监控运维</span></div>
        <div class="page-desc">跟踪采集成功率、缓存命中、数据完整性、API 性能和告警处理闭环。</div>
      </div>
      <div class="page-actions">
        <el-radio-group v-model="alertStatus" size="small" @change="loadAlertRecords">
          <el-radio-button label="open">未处理</el-radio-button>
          <el-radio-button label="resolved">已处理</el-radio-button>
          <el-radio-button label="ignored">已忽略</el-radio-button>
          <el-radio-button label="">全部</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <div class="cards" v-if="metrics">
      <StatCard label="采集成功率" :value="metrics.crawl_success_rate" suffix="%" color="#20c997" :icon="CircleCheck" :bar-width="metrics.crawl_success_rate + '%'" sub="运行成功占比" />
      <StatCard label="缓存命中率" :value="metrics.cache.hit_rate" suffix="%" color="#35d0ba" :icon="Lightning" :bar-width="metrics.cache.hit_rate + '%'" :sub="`命中 ${metrics.cache.hits} / 未命中 ${metrics.cache.misses}`" />
      <StatCard label="运行总次数" :value="metrics.total_runs" color="#7aa2f7" :icon="Histogram" sub="累计采集运行" />
      <StatCard label="存储占用(MB)" :value="dbSize" color="#f2b84b" :icon="Coin" sub="数据库文件大小" />
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-head">
              <div class="section-title"><el-icon><DataAnalysis /></el-icon><span>数据完整性检查</span></div>
              <span class="text-dim small">近 30 个交易日，节假日已剔除</span>
            </div>
          </template>
          <el-table :data="integrity" height="380" size="small" empty-text="暂无数据">
            <el-table-column prop="name" label="名称" width="132" show-overflow-tooltip />
            <el-table-column prop="code" label="代码" width="112" />
            <el-table-column label="类型" width="72">
              <template #default="{ row }">{{ row.asset_type === 'stock' ? '股票' : '基金' }}</template>
            </el-table-column>
            <el-table-column label="完整率" min-width="170">
              <template #default="{ row }">
                <div class="comp">
                  <el-progress :percentage="row.completeness" :stroke-width="8" :color="compColor(row.completeness)" :show-text="false" />
                  <span class="mono-num" :style="{ color: compColor(row.completeness) }">{{ row.completeness }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="实际/应有" width="104">
              <template #default="{ row }">{{ row.actual }}/{{ row.expected }}</template>
            </el-table-column>
            <el-table-column prop="latest" label="最新日期" width="122" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-head">
              <div class="section-title"><el-icon><Warning /></el-icon><span>当前告警</span></div>
              <el-badge :value="alerts.length" :max="99" type="danger" v-if="alerts.length" />
            </div>
          </template>
          <div class="alert-list" v-if="alerts.length">
            <div v-for="(a, i) in alerts" :key="i" class="alert-item" :class="a.level">
              <el-icon class="a-icon"><WarningFilled v-if="a.level === 'error'" /><Warning v-else /></el-icon>
              <div class="a-body">
                <div class="a-head"><span class="a-type">{{ a.type }}</span><span class="a-target">{{ a.target }}</span></div>
                <div class="a-msg">{{ a.message }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无告警，系统运行正常" :image-size="84" />
        </el-card>
      </el-col>
    </el-row>

    <el-card v-loading="loading">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><Connection /></el-icon><span>API 服务性能</span></div>
          <span class="text-dim small">请求数、平均耗时、峰值耗时和错误率</span>
        </div>
      </template>
      <el-table :data="apiStats" height="300" size="small" empty-text="暂无请求记录">
        <el-table-column prop="path" label="接口路径" min-width="220" show-overflow-tooltip />
        <el-table-column prop="count" label="请求数" width="90" sortable />
        <el-table-column label="平均耗时" width="112" sortable :sort-by="(r) => r.avg_ms"><template #default="{ row }"><span class="mono-num">{{ row.avg_ms }} ms</span></template></el-table-column>
        <el-table-column label="峰值" width="104"><template #default="{ row }"><span class="mono-num">{{ row.max_ms }} ms</span></template></el-table-column>
        <el-table-column label="错误率" width="104"><template #default="{ row }"><span :class="row.error_rate > 0 ? 'text-up' : 'text-sub'">{{ row.error_rate }}%</span></template></el-table-column>
      </el-table>
    </el-card>

    <el-card v-loading="recordLoading">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><Tickets /></el-icon><span>告警处理历史</span></div>
          <span class="text-dim small">记录去重、状态流转和处理人</span>
        </div>
      </template>
      <el-table :data="alertRecords" height="360" size="small" empty-text="暂无告警记录">
        <el-table-column label="级别" width="80"><template #default="{ row }"><el-tag size="small" :type="row.level === 'error' ? 'danger' : 'warning'">{{ row.level }}</el-tag></template></el-table-column>
        <el-table-column prop="alert_type" label="类型" width="130" show-overflow-tooltip />
        <el-table-column prop="target" label="对象" width="140" show-overflow-tooltip />
        <el-table-column prop="message" label="消息" min-width="240" show-overflow-tooltip />
        <el-table-column label="状态" width="92"><template #default="{ row }"><el-tag size="small" :type="recordStatusType(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="dispatch_status" label="分发" width="88" />
        <el-table-column prop="resolved_by" label="处理人" width="92" />
        <el-table-column prop="created_at" label="创建时间" width="160" :formatter="fmtTime" />
        <el-table-column label="操作" width="130" fixed="right" v-if="auth.isAdmin">
          <template #default="{ row }">
            <template v-if="row.status === 'open'">
              <el-button link type="success" size="small" @click="resolveAlert(row, 'resolved')">处理</el-button>
              <el-button link type="info" size="small" @click="resolveAlert(row, 'ignored')">忽略</el-button>
            </template>
            <span v-else class="text-dim small">已结束</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next" :total="recordTotal" :page-size="recordPageSize" :current-page="recordPage" @current-change="onRecordPage" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import StatCard from '../components/StatCard.vue'
import { CircleCheck, Lightning, Histogram, Coin, Warning, WarningFilled, Refresh, Monitor, DataAnalysis, Connection, Tickets } from '@element-plus/icons-vue'

const auth = useAuthStore()
const loading = ref(false)
const recordLoading = ref(false)
const metrics = ref(null)
const integrity = ref([])
const alerts = ref([])
const apiStats = ref([])
const alertRecords = ref([])
const alertStatus = ref('open')
const recordPage = ref(1)
const recordPageSize = 20
const recordTotal = ref(0)

const dbSize = computed(() => metrics.value?.db_size_mb ? Math.round(metrics.value.db_size_mb) : 0)

function compColor(v) { return v >= 90 ? '#20c997' : v >= 70 ? '#f2b84b' : '#ef4e5a' }
function statusText(s) { return { open: '未处理', resolved: '已处理', ignored: '已忽略' }[s] || s }
function recordStatusType(s) { return { open: 'danger', resolved: 'success', ignored: 'info' }[s] || 'info' }
function fmtTime(row, col, val) { return val ? val.replace('T', ' ').slice(0, 19) : '-' }

async function loadAlertRecords() {
  recordLoading.value = true
  try {
    const { data } = await api.alertRecords({ status: alertStatus.value || undefined, page: recordPage.value, page_size: recordPageSize })
    alertRecords.value = data.items
    recordTotal.value = data.total
  } finally { recordLoading.value = false }
}
function onRecordPage(p) { recordPage.value = p; loadAlertRecords() }
async function resolveAlert(row, status) {
  try {
    const { value } = await ElMessageBox.prompt('填写处理说明（可选）', status === 'resolved' ? '处理告警' : '忽略告警', {
      confirmButtonText: '确定', cancelButtonText: '取消', inputValue: '',
    })
    await api.resolveAlert(row.id, { status, note: value || '' })
    ElMessage.success('告警状态已更新')
    await Promise.all([loadAlertRecords(), loadCurrentAlerts()])
  } catch (e) { /* 取消 */ }
}
async function loadCurrentAlerts() {
  const { data } = await api.alerts()
  alerts.value = data
}
async function loadAll() {
  loading.value = true
  try {
    const [m, ig, st] = await Promise.all([api.metrics(), api.integrity(), api.apiStats()])
    metrics.value = m.data
    integrity.value = ig.data
    apiStats.value = st.data
    await Promise.all([loadCurrentAlerts(), loadAlertRecords()])
  } finally { loading.value = false }
}

onMounted(loadAll)
</script>

<style scoped>
.cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.small { font-size: 12px; }
.comp { display: flex; align-items: center; gap: 10px; }
.comp .el-progress { flex: 1; }
.alert-list { max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.alert-item { display: flex; gap: 12px; padding: 12px 14px; border-radius: 8px; background: rgba(255,255,255,0.035); border-left: 3px solid var(--warn); }
.alert-item.error { border-left-color: var(--danger); }
.a-icon { font-size: 18px; color: var(--warn); margin-top: 2px; }
.alert-item.error .a-icon { color: var(--danger); }
.a-head { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.a-type { font-weight: 650; color: var(--text-main); font-size: 13px; }
.a-target { font-size: 12px; color: var(--text-sub); }
.a-msg { font-size: 12px; color: var(--text-dim); line-height: 1.5; }
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
