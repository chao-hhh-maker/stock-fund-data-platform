<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Connection /></el-icon><span>数据源接入</span></div>
        <div class="page-desc">展示开源 SDK、公开网站、商业 API 和离线兜底源的启用状态、命中次数与最近使用时间。</div>
      </div>
      <div class="page-actions">
        <el-radio-group v-model="filter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="online">在线</el-radio-button>
          <el-radio-button label="fallback">兜底</el-radio-button>
          <el-radio-button label="offline">未启用</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="metric-grid summary-grid">
      <div class="metric-tile glass-card"><span class="metric-label">数据源总数</span><span class="metric-value mono-num">{{ sources.length }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">在线可用</span><span class="metric-value mono-num text-down">{{ counts.online }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">兜底源</span><span class="metric-value mono-num text-accent">{{ counts.fallback }}</span></div>
      <div class="metric-tile glass-card"><span class="metric-label">未启用</span><span class="metric-value mono-num text-dim">{{ counts.offline }}</span></div>
    </div>

    <div class="grid" v-loading="loading">
      <el-card v-for="s in filteredSources" :key="s.key" class="src-card" :class="s.status">
        <div class="src-head">
          <div>
            <div class="src-name">{{ s.name }}</div>
            <div class="src-cat">{{ s.category }}</div>
          </div>
          <el-tag :type="statusType(s.status)" effect="plain" size="small" round>{{ statusText(s.status) }}</el-tag>
        </div>
        <div class="src-desc">{{ s.description }}</div>
        <div class="src-foot">
          <span class="mono-num">命中 {{ s.hit_count }}</span>
          <span>{{ s.last_used || '尚未使用' }}</span>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && !filteredSources.length" description="暂无匹配数据源" :image-size="90" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { Connection, Refresh } from '@element-plus/icons-vue'
import api from '../api'

const sources = ref([])
const filter = ref('all')
const loading = ref(false)

const filteredSources = computed(() => filter.value === 'all' ? sources.value : sources.value.filter((s) => s.status === filter.value))
const counts = computed(() => ({
  online: sources.value.filter((s) => s.status === 'online').length,
  fallback: sources.value.filter((s) => s.status === 'fallback').length,
  offline: sources.value.filter((s) => s.status === 'offline').length,
}))
function statusType(s) { return s === 'online' ? 'success' : s === 'fallback' ? 'warning' : 'info' }
function statusText(s) { return { online: '在线可用', offline: '未启用', fallback: '兜底命中', unknown: '未知' }[s] || s }
async function load() {
  loading.value = true
  try {
    const { data } = await api.datasources()
    sources.value = data
  } finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.summary-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.src-card { border-left: 3px solid var(--border-soft) !important; }
.src-card.online { border-left-color: var(--down) !important; }
.src-card.fallback { border-left-color: var(--warn) !important; }
.src-card.offline { border-left-color: var(--text-dim) !important; opacity: 0.86; }
.src-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.src-name { font-size: 15px; font-weight: 700; color: var(--text-main); }
.src-cat { font-size: 12px; color: var(--accent); margin-top: 5px; }
.src-desc { font-size: 12px; color: var(--text-sub); min-height: 44px; line-height: 1.6; margin-top: 10px; }
.src-foot { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: var(--text-dim); margin-top: 12px; border-top: 1px solid var(--border-soft); padding-top: 10px; }
</style>
