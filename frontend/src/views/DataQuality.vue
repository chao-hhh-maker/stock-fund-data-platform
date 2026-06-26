<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><DataAnalysis /></el-icon><span>数据质量</span></div>
        <div class="page-desc">集中处理缺失值、异常值和跨源偏差，保留校对状态与处理说明。</div>
      </div>
      <div class="page-actions">
        <el-radio-group v-model="statusFilter" size="small" @change="reload">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="open">待处理</el-radio-button>
          <el-radio-button label="resolved">已修正</el-radio-button>
          <el-radio-button label="ignored">已忽略</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="metric-grid quality-summary">
      <div class="metric-tile glass-card"><span class="metric-label">当前筛选记录</span><span class="metric-value mono-num">{{ total }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">待处理</span><span class="metric-value mono-num text-up">{{ openCount }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">管理员操作</span><span class="metric-value quality-role">{{ auth.isAdmin ? '可处理' : '只读' }}</span></div>
    </div>

    <el-card v-loading="loading">
      <el-table :data="issues" height="520" size="small" empty-text="暂无数据质量问题">
        <el-table-column label="类型" width="112">
          <template #default="{ row }"><el-tag :type="typeTag(row.issue_type)" size="small">{{ typeText(row.issue_type) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="code" label="标的" width="122" />
        <el-table-column prop="dataset" label="数据集" width="112" />
        <el-table-column label="级别" width="84"><template #default="{ row }"><el-tag :type="sevTag(row.severity)" size="small" effect="plain">{{ row.severity }}</el-tag></template></el-table-column>
        <el-table-column prop="message" label="问题描述" min-width="280" show-overflow-tooltip />
        <el-table-column label="状态" width="96"><template #default="{ row }"><el-tag :type="statusTag(row.status)" size="small">{{ statusText(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="resolved_by" label="处理人" width="100" />
        <el-table-column label="操作" width="150" v-if="auth.isAdmin">
          <template #default="{ row }">
            <template v-if="row.status === 'open'">
              <el-button link type="success" size="small" @click="resolve(row, 'resolved')">修正</el-button>
              <el-button link type="info" size="small" @click="resolve(row, 'ignored')">忽略</el-button>
            </template>
            <span v-else class="text-dim small">已结束</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next" :total="total" :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, DataAnalysis } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const issues = ref([])
const statusFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
const openCount = computed(() => issues.value.filter((i) => i.status === 'open').length)

function typeText(t) { return { cross_source: '跨源偏差', anomaly: '字段异常', missing: '数据缺失' }[t] || t }
function typeTag(t) { return { cross_source: 'warning', anomaly: 'danger', missing: 'info' }[t] || '' }
function sevTag(s) { return { error: 'danger', warning: 'warning', info: 'info' }[s] || '' }
function statusText(s) { return { open: '待处理', resolved: '已修正', ignored: '已忽略' }[s] || s }
function statusTag(s) { return { open: 'danger', resolved: 'success', ignored: 'info' }[s] || 'info' }
async function load() {
  loading.value = true
  try {
    const { data } = await api.dataQuality({ status: statusFilter.value || undefined, page: page.value, page_size: pageSize })
    issues.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}
function reload() { page.value = 1; load() }
function onPage(p) { page.value = p; load() }
async function resolve(row, status) {
  try {
    const { value } = await ElMessageBox.prompt('填写校对说明（可选）', status === 'resolved' ? '标记为已修正' : '标记为已忽略', {
      confirmButtonText: '确定', cancelButtonText: '取消', inputValue: '',
    })
    await api.resolveIssue(row.id, { status, note: value || '' })
    ElMessage.success('已处理')
    load()
  } catch (e) { /* 取消 */ }
}
onMounted(load)
</script>

<style scoped>
.quality-summary { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.quality-role { font-size: 19px; color: var(--accent); }
.pager { margin-top: 14px; justify-content: flex-end; }
.small { font-size: 12px; }
</style>
