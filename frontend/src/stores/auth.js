import { defineStore } from 'pinia'
import http from '../api/http'

// 认证状态：token 与用户权限持久化到 localStorage
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
    dataScope: localStorage.getItem('dataScope') || 'all',
    maxHistoryDays: Number(localStorage.getItem('maxHistoryDays') || 0),
    canExport: localStorage.getItem('canExport') !== 'false',
    canViewSensitive: localStorage.getItem('canViewSensitive') === 'true',
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.role === 'admin',
    roleLabel: (s) => ({ admin: '管理员', viewer: '普通用户', analyst: '研究员' }[s.role] || s.role || '用户'),
  },
  actions: {
    _applyAuth(data) {
      this.token = data.access_token || this.token
      this.username = data.username || this.username
      this.role = data.role || this.role
      this.dataScope = data.data_scope || 'all'
      this.maxHistoryDays = Number(data.max_history_days || 0)
      this.canExport = data.can_export !== false
      this.canViewSensitive = data.can_view_sensitive === true
      localStorage.setItem('token', this.token)
      localStorage.setItem('username', this.username)
      localStorage.setItem('role', this.role)
      localStorage.setItem('dataScope', this.dataScope)
      localStorage.setItem('maxHistoryDays', String(this.maxHistoryDays))
      localStorage.setItem('canExport', String(this.canExport))
      localStorage.setItem('canViewSensitive', String(this.canViewSensitive))
    },
    async login(username, password) {
      const { data } = await http.post('/auth/login', { username, password })
      this._applyAuth(data)
      return data
    },
    async refreshMe() {
      if (!this.token) return null
      const { data } = await http.get('/auth/me')
      this._applyAuth({
        username: data.username,
        role: data.role,
        data_scope: data.data_scope,
        max_history_days: data.max_history_days,
        can_export: data.can_export,
        can_view_sensitive: data.can_view_sensitive,
      })
      return data
    },
    logout() {
      this.token = ''
      this.username = ''
      this.role = ''
      this.dataScope = 'all'
      this.maxHistoryDays = 0
      this.canExport = true
      this.canViewSensitive = false
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('dataScope')
      localStorage.removeItem('maxHistoryDays')
      localStorage.removeItem('canExport')
      localStorage.removeItem('canViewSensitive')
    },
  },
})
