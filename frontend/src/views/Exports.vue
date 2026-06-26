<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Download /></el-icon><span>数据导出</span></div>
        <div class="page-desc">按当前角色的数据权限导出 CSV、Excel 或 Parquet，并保留导出历史、压缩和加密信息。</div>
      </div>
      <div class="page-actions">
        <span class="source-chip">{{ scopeText }}</span>
        <el-button v-if="auth.canExport" type="primary" :icon="Plus" @click="dialog = true">新建导出</el-button>
      </div>
    </div>

    <el-alert v-if="!auth.canExport" type="warning" :closable="false" title="当前角色无导出权限，仅可查看本人历史导出记录" />

    <el-card v-loading="loadingList">
      <template #header><div class="section-title"><el-icon><Tickets /></el-icon><span>导出记录</span></div></template>
      <el-table :data="records" stripe empty-text="暂无导出记录">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="dataset" label="数据集" width="130" />
        <el-table-column prop="file_format" label="格式" width="90" />
        <el-table-column prop="file_name" label="文件名" show-overflow-tooltip />
        <el-table-column prop="row_count" label="行数" width="90" />
        <el-table-column prop="status" label="状态" width="90"><template #default="{ row }"><el-tag size="small" :type="row.status === 'success' ? 'success' : 'warning'">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column prop="created_at" label="时间" :formatter="fmtTime" />
        <el-table-column label="操作" width="110"><template #default="{ row }"><el-button size="small" type="primary" :disabled="row.status !== 'success'" :loading="downloadId === row.id" @click="download(row)">下载</el-button></template></el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next" :total="total" :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </el-card>

    <el-dialog v-model="dialog" title="新建数据导出" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="数据集"><el-select v-model="form.dataset"><el-option label="股票日线" value="stock_daily" /><el-option label="基金净值" value="fund_nav" /><el-option label="标的列表" value="instruments" /></el-select></el-form-item>
        <el-form-item label="格式"><el-select v-model="form.file_format"><el-option label="CSV" value="csv" /><el-option label="Excel" value="excel" /><el-option label="Parquet" value="parquet" /></el-select></el-form-item>
        <el-form-item label="代码(可选)"><el-input v-model="form.code" placeholder="如 600519.SH，留空导出全部" /></el-form-item>
        <el-form-item label="加密压缩"><el-checkbox v-model="form.compress">压缩为 ZIP</el-checkbox><el-checkbox v-model="form.encrypt">加密（需密码解压）</el-checkbox></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="submit" :loading="loading">导出</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Plus, Tickets } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const dialog = ref(false)
const loading = ref(false)
const loadingList = ref(false)
const downloadId = ref(null)
const form = reactive({ dataset: 'stock_daily', file_format: 'csv', code: '', compress: false, encrypt: false })
const scopeText = computed(() => {
  const scope = { all: '全部标的', stock: '股票', fund: '基金' }[auth.dataScope] || auth.dataScope
  const days = auth.maxHistoryDays > 0 ? `近 ${auth.maxHistoryDays} 天` : '不限时间'
  return `${scope} / ${days}`
})
function fmtTime(row, col, val) { return val ? val.replace('T', ' ').slice(0, 19) : '-' }
async function load() { loadingList.value = true; try { const { data } = await api.listExports({ page: page.value, page_size: pageSize }); records.value = data.items; total.value = data.total } finally { loadingList.value = false } }
function onPage(p) { page.value = p; load() }
async function submit() {
  if (!auth.canExport) { ElMessage.warning('当前角色无导出权限'); return }
  loading.value = true
  try {
    const body = { dataset: form.dataset, file_format: form.file_format, compress: form.compress, encrypt: form.encrypt }
    if (form.code) body.code = form.code.trim()
    await api.createExport(body)
    ElMessage.success(form.encrypt ? '导出成功（已加密，解压密码见后端配置）' : '导出成功')
    dialog.value = false
    page.value = 1
    await load()
  } finally { loading.value = false }
}
async function download(row) {
  downloadId.value = row.id
  try {
    const resp = await api.downloadExport(row.id)
    const url = window.URL.createObjectURL(new Blob([resp.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = row.file_name
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } finally { downloadId.value = null }
}
onMounted(load)
</script>

<style scoped>
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
