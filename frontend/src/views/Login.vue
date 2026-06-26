<template>
  <div class="login-wrapper">
    <section class="login-shell">
      <div class="product-panel">
        <div class="brand-row">
          <div class="brand-mark">D</div>
          <div>
            <div class="brand-title">量数 DataHub</div>
            <div class="brand-sub">股票基金数据获取和管理平台</div>
          </div>
        </div>
        <div class="product-title">数据采集、治理、查询与监控的一体化课程设计系统</div>
        <div class="cap-grid">
          <div class="cap"><span class="status-dot ok"></span>多源采集</div>
          <div class="cap"><span class="status-dot ok"></span>质量校验</div>
          <div class="cap"><span class="status-dot ok"></span>权限控制</div>
          <div class="cap"><span class="status-dot ok"></span>导出审计</div>
        </div>
        <div class="system-note">题目二 · 支持股票、基金、公告舆情、任务调度和监控运维闭环展示</div>
      </div>

      <div class="login-card">
        <div class="form-head">
          <div class="form-title">登录平台</div>
          <div class="form-sub">选择演示账号或输入自定义账号</div>
        </div>
        <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="onLogin" class="form">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" size="large" :prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" size="large" class="submit" :loading="loading" @click="onLogin">
            进入平台
          </el-button>
        </el-form>

        <div class="accounts">
          <button class="acc" @click="fill('admin', 'admin123')">
            <span class="tag admin">管理员</span><span>admin / admin123</span>
          </button>
          <button class="acc" @click="fill('viewer', 'viewer123')">
            <span class="tag viewer">普通用户</span><span>viewer / viewer123</span>
          </button>
          <button class="acc" @click="fill('analyst', 'analyst123')">
            <span class="tag analyst">研究员</span><span>analyst / analyst123</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function fill(u, p) { form.username = u; form.password = p }

async function onLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : '/dashboard'
    router.push(redirect)
  } catch (e) {
    // 错误已由拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}
.login-shell {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) 420px;
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  overflow: hidden;
  background: rgba(19, 24, 32, 0.86);
  box-shadow: var(--shadow-panel);
}
.product-panel {
  padding: 42px;
  border-right: 1px solid var(--border-soft);
  background:
    linear-gradient(135deg, rgba(53,208,186,0.08), transparent 38%),
    rgba(255,255,255,0.018);
}
.brand-row { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #06110f;
  font-weight: 800;
}
.brand-title { font-size: 19px; font-weight: 780; color: var(--text-main); }
.brand-sub { margin-top: 2px; color: var(--text-sub); font-size: 13px; }
.product-title { margin-top: 44px; max-width: 520px; font-size: 28px; line-height: 1.45; font-weight: 780; color: var(--text-main); }
.cap-grid { margin-top: 30px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.cap { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border: 1px solid var(--border-soft); border-radius: 8px; color: var(--text-sub); background: rgba(255,255,255,0.025); }
.system-note { margin-top: 28px; color: var(--text-dim); font-size: 13px; line-height: 1.7; }
.login-card { padding: 36px; background: rgba(10, 13, 18, 0.34); }
.form-head { margin-bottom: 22px; }
.form-title { font-size: 22px; font-weight: 760; color: var(--text-main); }
.form-sub { color: var(--text-dim); font-size: 13px; margin-top: 6px; }
.form { margin-bottom: 14px; }
.submit { width: 100%; margin-top: 4px; }
.accounts { display: flex; flex-direction: column; gap: 8px; margin-top: 18px; }
.acc {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-soft);
  background: rgba(255,255,255,0.025);
  color: var(--text-sub);
  cursor: pointer;
  text-align: left;
  font: inherit;
}
.acc:hover { border-color: var(--border-strong); color: var(--text-main); }
.tag { display: inline-flex; min-width: 64px; justify-content: center; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; }
.tag.admin { background: rgba(239, 78, 90, 0.16); color: #ff9ba4; }
.tag.viewer { background: rgba(122, 162, 247, 0.14); color: #a9c1ff; }
.tag.analyst { background: rgba(242, 184, 75, 0.16); color: #ffd37f; }
@media (max-width: 840px) {
  .login-shell { grid-template-columns: 1fr; }
  .product-panel { border-right: none; border-bottom: 1px solid var(--border-soft); padding: 28px; }
  .product-title { margin-top: 28px; font-size: 23px; }
  .login-card { padding: 28px; }
}
</style>
