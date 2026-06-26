import { ElMessage } from 'element-plus'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '数据驾驶舱' } },
      { path: 'stocks', name: 'stocks', component: () => import('../views/Stocks.vue'), meta: { title: '股票行情' } },
      { path: 'funds', name: 'funds', component: () => import('../views/Funds.vue'), meta: { title: '基金净值' } },
      { path: 'announcements', name: 'announcements', component: () => import('../views/Announcements.vue'), meta: { title: '公告舆情' } },
      { path: 'tasks', name: 'tasks', component: () => import('../views/Tasks.vue'), meta: { title: '采集任务' } },
      { path: 'datasources', name: 'datasources', component: () => import('../views/DataSources.vue'), meta: { title: '数据源接入' } },
      { path: 'quality', name: 'quality', component: () => import('../views/DataQuality.vue'), meta: { title: '数据质量' } },
      { path: 'monitor', name: 'monitor', component: () => import('../views/Monitor.vue'), meta: { title: '监控运维' } },
      { path: 'metadata', name: 'metadata', component: () => import('../views/Metadata.vue'), meta: { title: '元数据血缘' } },
      { path: 'query', name: 'query', component: () => import('../views/SqlQuery.vue'), meta: { title: 'SQL 查询台', admin: true } },
      { path: 'exports', name: 'exports', component: () => import('../views/Exports.vue'), meta: { title: '数据导出' } },
      { path: 'admin', name: 'admin', component: () => import('../views/Admin.vue'), meta: { title: '系统管理', admin: true } },
      { path: 'audit', name: 'audit', component: () => import('../views/Audit.vue'), meta: { title: '审计日志', admin: true } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局守卫：未登录跳转登录页；管理员页面拦截普通用户
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.name !== 'login' && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    const redirect = typeof to.query.redirect === 'string' && to.query.redirect.startsWith('/')
      ? to.query.redirect
      : '/dashboard'
    return { path: redirect }
  }
  if (to.meta?.admin && !auth.isAdmin) {
    ElMessage.warning('当前账号无权访问该页面')
    return { name: 'dashboard' }
  }
})

export default router
