<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <div class="page-title"><el-icon><Bell /></el-icon><span>公告舆情</span></div>
        <div class="page-desc">聚合上市公司公告、新闻和舆情记录，支持按类型筛选并保留来源信息。</div>
      </div>
      <div class="page-actions">
        <el-radio-group v-model="category" size="small" @change="reload">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="announcement">公告</el-radio-button>
          <el-radio-button label="report">年报/业绩</el-radio-button>
          <el-radio-button label="news">新闻</el-radio-button>
          <el-radio-button label="sentiment">舆情</el-radio-button>
        </el-radio-group>
        <el-button v-if="auth.isAdmin" type="primary" :icon="Refresh" :loading="crawling" @click="crawl">采集</el-button>
      </div>
    </div>

    <el-card v-loading="loading">
      <div v-if="items.length" class="feed">
        <article v-for="a in items" :key="a.id" class="item">
          <div class="item-head">
            <el-tag :type="catTag(a.category)" size="small">{{ catText(a.category) }}</el-tag>
            <span class="senti" :class="a.sentiment">{{ sentiText(a.sentiment) }}</span>
            <span class="source-chip">{{ a.source }}</span>
            <span class="date mono-num">{{ a.publish_date }}</span>
          </div>
          <div class="title">{{ a.title }}</div>
          <div class="summary">{{ a.summary }}</div>
          <div class="meta">
            <span v-if="a.code" class="code mono-num">{{ a.code }}</span>
            <el-button v-if="a.url" link size="small" :icon="Link" @click="openUrl(a.url)">原文</el-button>
          </div>
        </article>
      </div>
      <el-empty v-else description="暂无公告舆情数据" :image-size="90" />
      <el-pagination v-if="total > pageSize" class="pager" layout="total, prev, pager, next" :total="total" :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, Refresh, Link } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const items = ref([])
const category = ref('')
const page = ref(1)
const pageSize = 12
const total = ref(0)
const crawling = ref(false)
const loading = ref(false)

function catText(c) { return { announcement: '公告', report: '年报/业绩', news: '新闻', sentiment: '舆情' }[c] || c }
function catTag(c) { return { announcement: 'primary', report: 'success', news: 'info', sentiment: 'warning' }[c] || '' }
function sentiText(s) { return { positive: '正面', neutral: '中性', negative: '负面' }[s] || s }
function openUrl(url) { window.open(url, '_blank', 'noopener,noreferrer') }
async function load() {
  loading.value = true
  try {
    const { data } = await api.announcements({ category: category.value || undefined, page: page.value, page_size: pageSize })
    items.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}
function reload() { page.value = 1; load() }
function onPage(p) { page.value = p; load() }
async function crawl() {
  crawling.value = true
  try {
    await api.quickCrawl({ job_type: 'announcement', target_codes: '', mode: 'full' })
    ElMessage.success('采集完成')
    reload()
  } finally { crawling.value = false }
}
onMounted(load)
</script>

<style scoped>
.feed { display: flex; flex-direction: column; gap: 12px; }
.item { padding: 14px 16px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-soft); }
.item-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.senti { font-size: 12px; padding: 2px 8px; border-radius: 999px; font-weight: 650; }
.senti.positive { color: var(--down); background: rgba(32,201,151,0.12); }
.senti.neutral { color: var(--text-sub); background: rgba(255,255,255,0.06); }
.senti.negative { color: var(--up); background: rgba(240,100,100,0.12); }
.date { margin-left: auto; color: var(--text-dim); font-size: 12px; }
.title { font-size: 15px; font-weight: 700; color: var(--text-main); line-height: 1.55; margin-bottom: 5px; }
.summary { font-size: 13px; color: var(--text-sub); line-height: 1.65; }
.meta { display: flex; align-items: center; gap: 12px; margin-top: 10px; font-size: 12px; color: var(--text-dim); }
.code { color: var(--accent); }
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
