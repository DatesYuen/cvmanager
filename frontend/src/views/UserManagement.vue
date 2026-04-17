<template>
  <div>
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 新增用户
      </el-button>
    </div>
    <div class="card-container">
      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="(v, k) in row.permissions" :key="k" size="small"
                    :type="v ? 'success' : 'info'" style="margin:2px">
              {{ k }}: {{ v ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card-container" style="margin-top:20px">
      <div class="page-header" style="margin-bottom:16px">
        <h2 style="font-size:18px">AI 审核配置</h2>
        <div style="display:flex; gap:12px">
          <el-button @click="testAiSettings" :loading="testingAi">测试AI服务</el-button>
          <el-button type="primary" @click="saveAiSettings" :loading="savingAi">保存 AI 配置</el-button>
        </div>
      </div>
      <el-form :model="aiSettings" label-width="140px">
        <el-form-item label="Responses URL">
          <el-input v-model="aiSettings.response_api_url" placeholder="https://api.openai.com/v1/responses" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="aiSettings.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="aiSettings.model" placeholder="gpt-4.1-mini" />
        </el-form-item>
        <el-form-item label="AI审核阈值">
          <div style="display:flex; align-items:center; gap:12px; width:100%">
            <el-slider v-model="aiThresholdPercent" :min="0" :max="100" :step="5" style="flex:1" />
            <span style="width:52px; text-align:right">{{ aiThresholdPercent }}%</span>
          </div>
        </el-form-item>
        <el-form-item label="并发数">
          <el-input-number v-model="aiSettings.ai_review_concurrency" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="失败重试次数">
          <el-input-number v-model="aiSettings.ai_review_retry_count" :min="0" :max="5" />
        </el-form-item>
        <el-form-item label="Prompt 模板">
          <el-input v-model="aiSettings.prompt_template" type="textarea" :rows="12" />
        </el-form-item>
        <div style="color:#909399; font-size:13px; line-height:1.8">
          可用占位符：
          <code v-pre>{{ origin_text }}</code>、
          <code v-pre>{{ text_class }}</code>、
          <code v-pre>{{ return_format }}</code>。
          系统在发送给 AI 前会自动替换。
        </div>
      </el-form>
      <div v-if="aiTestResult" style="margin-top:16px">
        <el-alert :title="aiTestResult" :type="aiTestSuccess ? 'success' : 'error'" :closable="false" show-icon />
      </div>
    </div>

    <el-dialog v-model="showAddDialog" :title="editMode === 'add' ? '新增用户' : '编辑用户'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="editMode === 'edit'" />
        </el-form-item>
        <el-form-item label="密码" v-if="editMode === 'add'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-divider>权限设置</el-divider>
        <el-form-item v-for="perm in permissionList" :key="perm.key" :label="perm.label">
          <el-switch v-model="form.permissions[perm.key]" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editMode = ref('add')
const saving = ref(false)
const savingAi = ref(false)
const testingAi = ref(false)
const editingId = ref(null)
const aiSettings = ref({
  response_api_url: 'https://api.openai.com/v1/responses',
  api_key: '',
  model: 'gpt-4.1-mini',
  prompt_template: '',
  ai_review_confidence_threshold: 0.6,
  ai_review_concurrency: 2,
  ai_review_retry_count: 1,
})

const permissionList = [
  { key: 'can_create_person', label: '创建人员' },
  { key: 'can_edit_person', label: '编辑人员' },
  { key: 'can_delete_person', label: '删除人员' },
  { key: 'can_upload_resume', label: '上传简历' },
  { key: 'can_review', label: '审核权限' },
  { key: 'can_export', label: '导出权限' },
]

const defaultForm = () => ({
  username: '', password: '', display_name: '', role: 'user', is_active: true,
  permissions: Object.fromEntries(permissionList.map(p => [p.key, false]))
})

const form = ref(defaultForm())
const aiThresholdPercent = ref(60)
const aiTestResult = ref('')
const aiTestSuccess = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const res = await api.get('/api/users/')
    users.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadAiSettings() {
  const res = await api.get('/api/ai/settings')
  aiSettings.value = res.data
  aiThresholdPercent.value = Math.round((res.data.ai_review_confidence_threshold || 0.6) * 100)
}

function editUser(row) {
  editMode.value = 'edit'
  editingId.value = row.id
  form.value = {
    username: row.username,
    display_name: row.display_name || '',
    role: row.role,
    is_active: row.is_active,
    permissions: { ...Object.fromEntries(permissionList.map(p => [p.key, false])), ...row.permissions },
  }
  showAddDialog.value = true
}

async function saveUser() {
  saving.value = true
  try {
    if (editMode.value === 'add') {
      await api.post('/api/users/', form.value)
      ElMessage.success('创建成功')
    } else {
      const data = { ...form.value }
      delete data.username
      await api.put(`/api/users/${editingId.value}`, data)
      ElMessage.success('更新成功')
    }
    showAddDialog.value = false
    form.value = defaultForm()
    editMode.value = 'add'
    await loadUsers()
  } finally {
    saving.value = false
  }
}

async function saveAiSettings() {
  savingAi.value = true
  try {
    const payload = {
      ...aiSettings.value,
      ai_review_confidence_threshold: aiThresholdPercent.value / 100,
    }
    const res = await api.put('/api/ai/settings', payload)
    aiSettings.value = res.data
    aiThresholdPercent.value = Math.round((res.data.ai_review_confidence_threshold || 0.6) * 100)
    ElMessage.success('AI 配置已保存')
  } finally {
    savingAi.value = false
  }
}

async function testAiSettings() {
  testingAi.value = true
  aiTestResult.value = ''
  try {
    await api.put('/api/ai/settings', {
      ...aiSettings.value,
      ai_review_confidence_threshold: aiThresholdPercent.value / 100,
    })
    const res = await api.post('/api/ai/test', {
      sample_text: 'Shanchen Pang, Teng Wang, Haiyuan Gui, Xiao He, Lili Hou, An intelligent task offloading method based on multi-agent deep reinforcement learning in ultra-dense heterogeneous network with mobile edge computing[J],Computer Networks,2024,110555,ISSN 1389-1286, https://doi.org/10.1016/j.comnet.2024.110555.',
      entity_type: 'papers',
    })
    aiTestSuccess.value = true
    aiTestResult.value = `${res.data.message} 返回示例：${JSON.stringify(res.data.parsed_result)}`
  } catch (e) {
    aiTestSuccess.value = false
    aiTestResult.value = 'AI服务测试失败，请检查 URL、API Key、模型和 Prompt。'
  } finally {
    testingAi.value = false
  }
}

async function deleteUser(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 "${row.username}" 吗？`, '确认删除', { type: 'warning' })
    await api.delete(`/api/users/${row.id}`)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (e) {}
}

onMounted(async () => {
  await loadUsers()
  await loadAiSettings()
})
</script>
