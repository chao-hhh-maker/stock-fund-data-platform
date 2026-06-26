<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '72px' : '244px'" class="aside">
      <div class="brand" :class="{ compact: collapsed }">
        <div class="brand-mark">D</div>
        <div v-show="!collapsed" class="brand-copy">
          <div class="brand-name">量数 DataHub</div>
          <div class="brand-sub">股票基金数据平台</div>
        </div>
      </div>

      <el-menu :default-active="route.name" :default-openeds="openedGroups" :collapse="collapsed" router class="menu">
        <template v-for="g in visibleGroups" :key="g.title">
          <el-menu-item v-if="g.items.length === 1 && g.flat" :index="g.items[0].name" :route="{ name: g.items[0].name }">
            <el-icon><component :is="g.items[0].icon" /></el-icon>
            <template #title>{{ g.items[0].title }}</template>
          </el-menu-item>
          <el-sub-menu v-else :index="g.title">
            <template #title>
              <el-icon><component :is="g.icon" /></el-icon>
              <span>{{ g.title }}</span>
            </template>
            <el-menu-item v-for="m in g.items" :key="m.name" :index="m.name" :route="{ name: m.name }">
              <el-icon><component :is="m.icon" /></el-icon>
              <template #title>{{ m.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>

      <div class="aside-foot" v-show="!collapsed">
        <div class="status-line">
          <span class="status-dot" :class="health ? 'ok' : 'warn'"></span>
          {{ health ? '后端服务正常' : '正在连接后端' }}
        </div>
        <div class="foot-meta mono-num">{{ now }}</div>
      </div>
    </el-aside>

    <el-container class="content-wrap">
      <el-header class="header">
        <div class="header-left">
          <el-tooltip :content="collapsed ? '展开菜单' : '收起菜单'" placement="bottom">
            <el-button text class="icon-btn" @click="collapsed = !collapsed">
              <el-icon><Fold /></el-icon>
            </el-button>
          </el-tooltip>
          <div>
            <div class="title">{{ route.meta.title }}</div>
            <div class="breadcrumb">题目二 · 数据获取 · 清洗治理 · 查询服务 · 监控运维</div>
          </div>
        </div>
        <div class="user-panel">
          <el-tag :type="roleTag" effect="plain" round>{{ auth.roleLabel }}</el-tag>
          <el-tag effect="plain" round>{{ scopeLabel }}</el-tag>
          <el-tag :type="auth.canExport ? 'success' : 'warning'" effect="plain" round>{{ exportLabel }}</el-tag>
          <el-avatar :size="32" class="avatar">{{ avatarInitial }}</el-avatar>
          <span class="username">{{ auth.username || '未登录' }}</span>
          <el-tooltip content="退出登录" placement="bottom">
            <el-button text class="icon-btn danger" @click="onLogout">
              <el-icon><SwitchButton /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import {
  DataBoard, TrendCharts, Money, Operation, Download,
  Monitor, Collection, Document, Fold, SwitchButton,
  Bell, Connection, DataAnalysis, MagicStick, Setting,
  Histogram, Cpu, Files,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const collapsed = ref(false)
const health = ref(false)
const now = ref('')

const groups = [
  { title: '数据驾驶舱', icon: DataBoard, flat: true, items: [
    { name: 'dashboard', title: '数据驾驶舱', icon: DataBoard },
  ] },
  { title: '行情数据', icon: TrendCharts, items: [
    { name: 'stocks', title: '股票行情', icon: TrendCharts },
    { name: 'funds', title: '基金净值', icon: Money },
    { name: 'announcements', title: '公告舆情', icon: Bell },
  ] },
  { title: '数据采集', icon: Operation, items: [
    { name: 'tasks', title: '采集任务', icon: Operation },
    { name: 'datasources', title: '数据源接入', icon: Connection },
  ] },
  { title: '数据治理', icon: Files, items: [
    { name: 'quality', title: '数据质量', icon: DataAnalysis },
    { name: 'metadata', title: '元数据血缘', icon: Collection },
  ] },
  { title: '查询服务', icon: Histogram, items: [
    { name: 'query', title: 'SQL 查询台', icon: MagicStick, admin: true },
    { name: 'exports', title: '数据导出', icon: Download },
  ] },
  { title: '监控运维', icon: Cpu, items: [
    { name: 'monitor', title: '监控运维', icon: Monitor },
    { name: 'admin', title: '系统管理', icon: Setting, admin: true },
    { name: 'audit', title: '审计日志', icon: Document, admin: true },
  ] },
]

const visibleGroups = computed(() =>
  groups
    .map((g) => ({ ...g, items: g.items.filter((m) => !m.admin || auth.isAdmin) }))
    .filter((g) => g.items.length > 0)
)
const openedGroups = computed(() => visibleGroups.value.map((g) => g.title))
const roleTag = computed(() => auth.isAdmin ? 'danger' : auth.role === 'analyst' ? 'warning' : 'info')
const avatarInitial = computed(() => (auth.username || 'U').slice(0, 1).toUpperCase())
const scopeLabel = computed(() => {
  const scope = { all: '全部数据', stock: '股票数据', fund: '基金数据' }[auth.dataScope] || auth.dataScope || '全部数据'
  const days = auth.maxHistoryDays > 0 ? `近${auth.maxHistoryDays}天` : '不限时间'
  return `${scope} · ${days}`
})
const exportLabel = computed(() => auth.canExport ? '可导出' : '禁导出')

let timer = null
function tick() {
  now.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(async () => {
  tick()
  timer = setInterval(tick, 1000)
  try { await auth.refreshMe() } catch (e) { /* token 失效由拦截器处理 */ }
  try {
    const { data } = await api.health()
    health.value = data.status === 'ok'
  } catch (e) { health.value = false }
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.layout { height: 100vh; overflow: hidden; }
.aside {
  background: rgba(12, 15, 20, 0.96);
  border-right: 1px solid var(--border-soft);
  transition: width 0.22s ease;
  display: flex;
  flex-direction: column;
}
.brand {
  min-height: 70px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border-soft);
}
.brand.compact { justify-content: center; padding: 0; }
.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #06110f;
  font-weight: 800;
}
.brand-name { font-size: 16px; font-weight: 760; color: var(--text-main); }
.brand-sub { font-size: 12px; color: var(--text-dim); margin-top: 2px; }
.menu { border-right: none; background: transparent; flex: 1; padding: 10px 8px; }
.menu :deep(.el-sub-menu__title),
.menu :deep(.el-menu-item) {
  color: var(--text-sub);
  border-radius: 8px;
  height: 42px;
  margin: 3px 0;
}
.menu :deep(.el-sub-menu__title:hover),
.menu :deep(.el-menu-item:hover) { color: var(--text-main); background: rgba(255,255,255,0.045); }
.menu :deep(.el-menu-item.is-active) {
  color: var(--accent);
  background: rgba(53, 208, 186, 0.11);
  box-shadow: inset 3px 0 0 var(--accent);
}
.aside-foot {
  padding: 14px 18px;
  border-top: 1px solid var(--border-soft);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.foot-meta { color: var(--text-dim); font-size: 12px; }
.content-wrap { min-width: 0; }
.header {
  height: 66px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(13, 17, 23, 0.82);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-soft);
  padding: 0 18px;
}
.header-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.icon-btn { width: 34px; height: 34px; padding: 0 !important; color: var(--text-sub); }
.icon-btn:hover { color: var(--accent); background: rgba(255,255,255,0.05) !important; }
.icon-btn.danger:hover { color: var(--danger); }
.title { font-size: 17px; font-weight: 730; color: var(--text-main); line-height: 1.25; }
.breadcrumb { color: var(--text-dim); font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-panel { display: flex; align-items: center; gap: 10px; min-width: 0; }
.avatar { background: var(--accent); color: #06110f; font-weight: 760; flex: 0 0 auto; }
.username { color: var(--text-sub); max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.main { background: transparent; padding: 18px; overflow-y: auto; }
.fade-slide-enter-active, .fade-slide-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(8px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-4px); }

@media (max-width: 900px) {
  .breadcrumb, .user-panel .el-tag { display: none; }
  .username { display: none; }
}
</style>
