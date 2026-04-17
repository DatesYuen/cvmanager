<template>
  <div>
    <div class="page-header">
      <h2>人员管理</h2>
      <div>
        <el-input v-model="search" placeholder="搜索人员" style="width:240px; margin-right:12px"
                  prefix-icon="Search" @input="loadPersons" clearable />
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon> 新增人员
        </el-button>
      </div>
    </div>
    <div class="card-container">
      <el-table :data="persons" stripe style="width:100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="150" />
        <el-table-column prop="name_en" label="英文名" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="360">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="$router.push(`/persons/${row.id}`)">
              查看详情
            </el-button>
            <el-button size="small" @click="$router.push(`/showcase/${row.id}`)">
              展示页
            </el-button>
            <el-button size="small" type="success" @click="$router.push(`/upload/${row.id}`)">
              上传简历
            </el-button>
            <el-button size="small" type="danger" @click="deletePerson(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showAddDialog" title="新增人员" width="400px">
      <el-form :model="newPerson" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="newPerson.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="英文名">
          <el-input v-model="newPerson.name_en" placeholder="可选，如 Shanchen Pang" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addPerson" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const persons = ref([])
const loading = ref(false)
const search = ref('')
const showAddDialog = ref(false)
const saving = ref(false)
const newPerson = ref({ name: '', name_en: '' })

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

async function loadPersons() {
  loading.value = true
  try {
    const params = search.value ? { search: search.value } : {}
    const res = await api.get('/api/persons/', { params })
    persons.value = res.data
  } finally {
    loading.value = false
  }
}

async function addPerson() {
  if (!newPerson.value.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  saving.value = true
  try {
    await api.post('/api/persons/', newPerson.value)
    ElMessage.success('新增成功')
    showAddDialog.value = false
    newPerson.value = { name: '', name_en: '' }
    await loadPersons()
  } finally {
    saving.value = false
  }
}

async function deletePerson(row) {
  try {
    await ElMessageBox.confirm(`确定删除人员 "${row.name}" 吗？此操作不可恢复。`, '确认删除', {
      type: 'warning'
    })
    await api.delete(`/api/persons/${row.id}`)
    ElMessage.success('删除成功')
    await loadPersons()
  } catch (e) {}
}

onMounted(loadPersons)
</script>
