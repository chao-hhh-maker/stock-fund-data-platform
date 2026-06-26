<template>
  <div>
    <el-tabs v-model="tab">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="toolbar">
          <span class="text-sub small">机构级 / 部门级隔离 · 功能权限按角色继承</span>
          <el-button type="primary" :icon="Plus" @click="openUserDialog()">新建用户</el-button>
        </div>
        <el-table :data="users" size="small" border>
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="full_name" label="姓名" width="120" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }"><el-tag size="small">{{ row.role }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="tenant_name" label="租户" width="100" />
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openUserDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removeUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 角色权限 -->
      <el-tab-pane label="角色权限" name="roles">
        <div class="text-sub small mb">数据权限（行级 data_scope / 时间 max_history_days）+ 功能权限（导出 / 敏感字段）</div>
        <el-table :data="roles" size="small" border>
          <el-table-column prop="name" label="角色" width="100" />
          <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
          <el-table-column label="数据范围" width="120">
            <template #default="{ row }">
              <el-select v-model="row.data_scope" size="small" @change="saveRole(row)">
                <el-option label="全部" value="all" />
                <el-option label="仅股票" value="stock" />
                <el-option label="仅基金" value="fund" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="历史天数(0=不限)" width="140">
            <template #default="{ row }">
              <el-input-number v-model="row.max_history_days" :min="0" size="small" controls-position="right"
                @change="saveRole(row)" style="width: 110px" />
            </template>
          </el-table-column>
          <el-table-column label="可导出" width="90">
            <template #default="{ row }">
              <el-switch v-model="row.can_export" @change="saveRole(row)" />
            </template>
          </el-table-column>
          <el-table-column label="敏感字段" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.can_view_sensitive" @change="saveRole(row)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 租户 -->
      <el-tab-pane label="租户(机构)" name="tenants">
        <div class="toolbar">
          <span class="text-sub small">机构级数据隔离</span>
          <el-button type="primary" :icon="Plus" @click="tenantDialog = true">新建租户</el-button>
        </div>
        <el-table :data="tenants" size="small" border>
          <el-table-column prop="code" label="编码" width="120" />
          <el-table-column prop="name" label="名称" width="160" />
          <el-table-column prop="description" label="说明" min-width="200" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 用户对话框 -->
    <el-dialog v-model="userDialog" :title="editingUser ? '编辑用户' : '新建用户'" width="460px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="userForm.username" :disabled="!!editingUser" /></el-form-item>
        <el-form-item :label="editingUser ? '新密码' : '密码'">
          <el-input v-model="userForm.password" type="password" :placeholder="editingUser ? '留空则不修改' : ''" />
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="userForm.full_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role_name" style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="租户">
          <el-select v-model="userForm.tenant_id" clearable style="width: 100%">
            <el-option v-for="t in tenants" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门"><el-input v-model="userForm.department" /></el-form-item>
        <el-form-item v-if="editingUser" label="状态">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 租户对话框 -->
    <el-dialog v-model="tenantDialog" title="新建租户" width="420px">
      <el-form :model="tenantForm" label-width="70px">
        <el-form-item label="编码"><el-input v-model="tenantForm.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="tenantForm.name" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="tenantForm.description" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tenantDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTenant">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../api'

const tab = ref('users')
const users = ref([])
const roles = ref([])
const tenants = ref([])

const userDialog = ref(false)
const editingUser = ref(null)
const userForm = reactive({ username: '', password: '', full_name: '', role_name: 'viewer', tenant_id: null, department: '', is_active: true })

const tenantDialog = ref(false)
const tenantForm = reactive({ code: '', name: '', description: '' })

async function loadAll() {
  const [u, r, t] = await Promise.all([api.adminUsers(), api.adminRoles(), api.adminTenants()])
  users.value = u.data
  roles.value = r.data
  tenants.value = t.data
}

function openUserDialog(row) {
  editingUser.value = row || null
  if (row) {
    Object.assign(userForm, { username: row.username, password: '', full_name: row.full_name, role_name: row.role, tenant_id: row.tenant_id, department: row.department, is_active: row.is_active })
  } else {
    Object.assign(userForm, { username: '', password: '', full_name: '', role_name: 'viewer', tenant_id: null, department: '', is_active: true })
  }
  userDialog.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      const body = { full_name: userForm.full_name, role_name: userForm.role_name, tenant_id: userForm.tenant_id, department: userForm.department, is_active: userForm.is_active }
      if (userForm.password) body.password = userForm.password
      await api.updateUser(editingUser.value.id, body)
    } else {
      await api.createUser({ username: userForm.username, password: userForm.password, role_name: userForm.role_name, full_name: userForm.full_name, tenant_id: userForm.tenant_id, department: userForm.department })
    }
    ElMessage.success('已保存')
    userDialog.value = false
    loadAll()
  } catch (e) { /* 错误已由拦截器提示 */ }
}

async function removeUser(row) {
  try {
    await ElMessageBox.confirm(`确认删除用户 ${row.username}？`, '提示', { type: 'warning' })
    await api.deleteUser(row.id)
    ElMessage.success('已删除')
    loadAll()
  } catch (e) { /* 取消 */ }
}

async function saveRole(row) {
  await api.updateRole(row.id, {
    data_scope: row.data_scope, max_history_days: row.max_history_days,
    can_export: row.can_export, can_view_sensitive: row.can_view_sensitive,
  })
  ElMessage.success(`角色 ${row.name} 权限已更新`)
}

async function saveTenant() {
  await api.createTenant({ ...tenantForm })
  ElMessage.success('已创建')
  tenantDialog.value = false
  Object.assign(tenantForm, { code: '', name: '', description: '' })
  loadAll()
}

onMounted(loadAll)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.small { font-size: 12px; }
.mb { margin-bottom: 12px; }
</style>
