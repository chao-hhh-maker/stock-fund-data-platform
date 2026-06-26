<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Collection /></el-icon><span>元数据血缘</span></div>
        <div class="page-desc">展示数据字典、字段敏感级别、数据来源、行数和时间范围，支撑数据管理与审计说明。</div>
      </div>
      <div class="page-actions"><el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button></div>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card v-loading="loading">
          <template #header><div class="section-title"><el-icon><Notebook /></el-icon><span>数据字典</span></div></template>
          <el-collapse v-model="active">
            <el-collapse-item v-for="t in dictionary" :key="t.table" :name="t.table">
              <template #title><span class="tbl-name">{{ t.table }}</span><span class="tbl-comment">{{ t.comment }}</span></template>
              <el-table :data="t.fields" size="small">
                <el-table-column prop="name" label="字段" width="150" />
                <el-table-column prop="type" label="类型" width="80" />
                <el-table-column prop="desc" label="说明" />
                <el-table-column label="敏感级别" width="96"><template #default="{ row }"><el-tag size="small" :type="sensTag(row.sensitivity)" effect="plain">{{ sensText(row.sensitivity) }}</el-tag></template></el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-head"><div class="section-title"><el-icon><Share /></el-icon><span>数据血缘</span></div><span class="text-dim small">来源、行数、时间范围追踪</span></div>
          </template>
          <el-table :data="lineage" height="520" size="small" empty-text="暂无数据">
            <el-table-column prop="code" label="代码" width="112" />
            <el-table-column label="数据集" width="112"><template #default="{ row }"><el-tag size="small" effect="plain" :type="row.dataset === 'stock_daily' ? 'primary' : 'warning'">{{ row.dataset === 'stock_daily' ? '股票日线' : '基金净值' }}</el-tag></template></el-table-column>
            <el-table-column label="来源" width="130"><template #default="{ row }"><span class="source-chip" :class="sourceClass(row.source)">{{ row.source }}</span></template></el-table-column>
            <el-table-column prop="rows" label="行数" width="88" />
            <el-table-column prop="earliest" label="起始" />
            <el-table-column prop="latest" label="最新" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Collection, Notebook, Share, Refresh } from '@element-plus/icons-vue'
import api from '../api'

const dictionary = ref([])
const lineage = ref([])
const active = ref(['instruments'])
const loading = ref(false)
function sensText(s) { return { public: '公开', internal: '内部', sensitive: '敏感' }[s] || '公开' }
function sensTag(s) { return { public: 'success', internal: 'warning', sensitive: 'danger' }[s] || 'success' }
function sourceClass(source = '') { return source.includes('sample') ? 'sample' : source ? 'real' : '' }
async function load() {
  loading.value = true
  try {
    const [d, l] = await Promise.all([api.dataDictionary(), api.lineage()])
    dictionary.value = d.data
    lineage.value = l.data
  } finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.small { font-size: 12px; }
.tbl-name { font-weight: 750; color: var(--accent); margin-right: 12px; }
.tbl-comment { color: var(--text-sub); font-size: 13px; }
</style>
