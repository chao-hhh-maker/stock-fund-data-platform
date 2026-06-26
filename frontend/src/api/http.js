import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import router from '../router'

// Axios 实例：统一 baseURL、token 注入、错误处理
const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

async function parseErrorDetail(error) {
  const data = error.response?.data
  if (data instanceof Blob) {
    try {
      const text = await data.text()
      const parsed = JSON.parse(text)
      return parsed?.detail || parsed?.message || error.message
    } catch (e) {
      return error.message
    }
  }
  return data?.detail || data?.message || error.message
}

function showError(status, detail, error) {
  if (!status) {
    ElMessage.error(error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '无法连接后端服务')
    return
  }
  if (status === 403) {
    ElMessage.error(typeof detail === 'string' ? detail : '无权限：当前账号不能执行该操作')
    return
  }
  if (status === 429) {
    ElMessage.error(typeof detail === 'string' ? detail : '操作过于频繁，请稍后再试')
    return
  }
  if (status >= 500) {
    ElMessage.error(typeof detail === 'string' ? `服务异常：${detail}` : '服务异常，请查看后端日志')
    return
  }
  ElMessage.error(typeof detail === 'string' ? detail : '请求失败')
}

// 请求拦截器：自动附加 JWT
http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截器：统一错误提示，401 自动登出
http.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    if (axios.isCancel(error)) return Promise.reject(error)

    const status = error.response?.status
    const detail = await parseErrorDetail(error)
    if (status === 401) {
      const auth = useAuthStore()
      auth.logout()
      if (router.currentRoute.value.name !== 'login') {
        ElMessage.error('登录已过期，请重新登录')
        router.push({ name: 'login' })
      }
    } else {
      showError(status, detail, error)
    }
    return Promise.reject(error)
  }
)

export default http
