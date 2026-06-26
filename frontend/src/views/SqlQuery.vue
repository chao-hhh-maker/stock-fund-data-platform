<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><MagicStick /></el-icon><span>SQL 查询台</span></div>
        <div class="page-desc">管理员只读查询入口：仅允许 SELECT、表名白名单、接口强制 LIMIT，并记录审计日志。</div>
      </div>
      <div class="page-actions"><el-tag type="warning" effect="plain">管理员</el-tag><el-tag effect="plain">只读 SELECT</el-tag></div>
    </div>

    <el-card>
      <template #header><div class="section-title"><el-icon><EditPen /></el-icon><span>查询语句</span></div></template>
      <el-input v-model="sql" type="textarea" :rows="6" class="mono-num sql-input" placeholder="例如：SELECT code, COUNT(*) AS n FROM stock_daily GROUP BY code ORDER BY n DESC" />
      <div class="bar">
        <div class="presets">
          <el-button v-for="(p, i) in presets" :key="i" link size="small" @click="sql = p.sql">{{ p.label }}</el-button>
        </div>
        <div class="actions">
          <span class="text-dim small">返回行数</span>
          <el-input-number v-model="limit" :min="1" :max="5000" size="small" />
          <el-button type="primary" :icon="Search" :loading="loading" @click="run">执行查询</el-button>
        </div>
      </div>
    </el-card>

    <el-card v-if="result" v-loading="loading">
      <template #header>
        <div class="card-head">
          <div class="section-title"><el-icon><Tickets /></el-icon><span>查询结果</span></div>
          <span class="text-sub small">{{ result.row_count }} 行 · {{ result.elapsed_ms }} ms <el-tag v-if="result.truncated" type="warning" size="small">已截断</el-tag></span>
        </div>
      </template>
      <el-table :data="result.rows" height="440" size="small" border>
        <el-table-column v-for="col in result.columns" :key="col" :prop="col" :label="col" show-overflow-tooltip min-width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, EditPen, Search, Tickets } from '@element-plus/icons-vue'
import api from '../api'

const sql = ref('SELECT code, COUNT(*) AS rows, MAX(trade_date) AS latest FROM stock_daily GROUP BY code ORDER BY rows DESC')
const limit = ref(200)
const loading = ref(false)
const result = ref(null)
const presets = [
  { label: '各股票行数', sql: 'SELECT code, COUNT(*) AS rows FROM stock_daily GROUP BY code ORDER BY rows DESC' },
  { label: '基金最新净值', sql: 'SELECT code, MAX(nav_date) AS latest FROM fund_nav GROUP BY code' },
  { label: '采集成功率', sql: "SELECT status, COUNT(*) AS n FROM crawl_runs GROUP BY status" },
  { label: '标的分类', sql: 'SELECT category, COUNT(*) AS n FROM instruments GROUP BY category ORDER BY n DESC' },
]
async function run() {
  loading.value = true
  try {
    const { data } = await api.runSql({ sql: sql.value, limit: limit.value })
    result.value = data
    ElMessage.success(`查询成功，返回 ${data.row_count} 行`)
  } finally { loading.value = false }
}
</script>

<style scoped>
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.small { font-size: 12px; }
.bar { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; flex-wrap: wrap; gap: 10px; }
.presets { display: flex; gap: 4px; flex-wrap: wrap; }
.actions { display: flex; align-items: center; gap: 10px; }
.sql-input :deep(.el-textarea__inner) { line-height: 1.65; }
</style>
