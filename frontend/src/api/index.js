import http from './http'

// 集中管理所有后端接口调用，便于维护
export const api = {
  me: () => http.get('/auth/me'),

  // 监控 / 仪表盘
  health: () => http.get('/health'),
  dashboard: () => http.get('/dashboard'),
  metrics: () => http.get('/monitor/metrics'),
  integrity: (params) => http.get('/monitor/integrity', { params }),
  alerts: () => http.get('/monitor/alerts'),
  apiStats: () => http.get('/monitor/api-stats'),
  alertRecords: (params) => http.get('/monitor/alert-records', { params }),
  resolveAlert: (id, body) => http.post(`/monitor/alert-records/${id}/resolve`, body),
  dataDictionary: () => http.get('/metadata/dictionary'),
  lineage: () => http.get('/metadata/lineage'),
  auditLogs: (params) => http.get('/audit/logs', { params }),

  // 数据源 / 公告 / 数据质量
  datasources: () => http.get('/datasources'),
  realtimeQuotes: () => http.get('/realtime/quotes'),
  announcements: (params) => http.get('/announcements', { params }),
  dataQuality: (params) => http.get('/data-quality', { params }),
  resolveIssue: (id, body) => http.post(`/data-quality/${id}/resolve`, body),

  // 标的与行情
  instruments: (params) => http.get('/instruments', { params }),
  stockDaily: (code, params) => http.get(`/stocks/${code}/daily`, { params }),
  fundNav: (code, params) => http.get(`/funds/${code}/nav`, { params }),

  // 受控 SQL 查询
  runSql: (body) => http.post('/query/sql', body),

  // 系统管理（用户 / 角色 / 租户）
  adminUsers: () => http.get('/admin/users'),
  createUser: (body) => http.post('/admin/users', body),
  updateUser: (id, body) => http.patch(`/admin/users/${id}`, body),
  deleteUser: (id) => http.delete(`/admin/users/${id}`),
  adminRoles: () => http.get('/admin/roles'),
  updateRole: (id, body) => http.patch(`/admin/roles/${id}`, body),
  adminTenants: () => http.get('/admin/tenants'),
  createTenant: (body) => http.post('/admin/tenants', body),

  // 采集任务
  listJobs: () => http.get('/tasks'),
  createJob: (body) => http.post('/tasks', body),
  updateJob: (id, body) => http.patch(`/tasks/${id}`, body),
  deleteJob: (id) => http.delete(`/tasks/${id}`),
  runJob: (id) => http.post(`/tasks/${id}/run`, null, { timeout: 120000 }),
  quickCrawl: (body) => http.post('/tasks/crawl', body, { timeout: 120000 }),
  crawlAll: (params) => http.post('/tasks/crawl-all', null, { params }),
  listRuns: (params) => http.get('/tasks/runs', { params }),
  jobLogs: (id, params) => http.get(`/tasks/${id}/logs`, { params }),

  // 导出
  createExport: (body) => http.post('/exports', body),
  listExports: (params) => http.get('/exports', { params }),
  downloadExport: (id) =>
    http.get(`/exports/${id}/download`, { responseType: 'blob' }),
}

// WebSocket 实时行情：返回 WebSocket 实例，token 通过 query 传递
export function openQuotesWs(token) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  // 经 vite 代理转发到后端 /api/ws/quotes
  const url = `${proto}://${location.host}/api/ws/quotes?token=${encodeURIComponent(token)}`
  return new WebSocket(url)
}

export default api

