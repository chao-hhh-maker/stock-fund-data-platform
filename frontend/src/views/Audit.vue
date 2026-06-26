<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-head">
          <span>🛡️ 操作审计日志</span>
          <span class="text-sub small">记录登录 / 采集 / 导出等关键操作</span>
        </div>
      </template>
      <el-table :data="logs" stripe empty-text="暂无审计记录">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="created_at" label="时间" width="180" :formatter="fmtTime" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            <el-tag size="small" effect="dark" :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="actionType(row.action)">{{ actionText(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="对象" width="140" show-overflow-tooltip />
        <el-table-column prop="detail" label="详情" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="130" />
      </el-table>
      <el-pagination class="mt" layout="total, prev, pager, next" :total="total"
        :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

function fmtTime(row, col, val) { return val ? val.replace('T', ' ').slice(0, 19) : '-' }
function actionText(a) {
  return { login: '登录', login_failed: '登录失败', crawl: '采集', export: '导出' }[a] || a
}
function actionType(a) {
  return { login: 'success', login_failed: 'danger', crawl: 'warning', export: 'primary' }[a] || 'info'
}

async function load() {
  const { data } = await api.auditLogs({ page: page.value, page_size: pageSize })
  logs.value = data.items
  total.value = data.total
}
function onPage(p) { page.value = p; load() }
onMounted(load)
</script>

<style scoped>
.card-head { display: flex; align-items: center; justify-content: space-between; }
.small { font-size: 12px; }
.mt { margin-top: 16px; }
</style>
