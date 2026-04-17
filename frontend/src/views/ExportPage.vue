<template>
  <div>
    <div class="page-header">
      <h2>数据导出</h2>
    </div>
    <div class="card-container" style="margin-bottom:20px">
      <h3 style="margin-bottom:16px">条目导出</h3>
      <el-form :model="exportForm" label-width="100px" :inline="false">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="数据类型">
              <el-select v-model="exportForm.entity_type" placeholder="选择类型" @change="loadFilterFields">
                <el-option v-for="t in entityTypes" :key="t.key" :label="t.label" :value="t.key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="人员">
              <el-select v-model="exportForm.person_id" placeholder="全部人员" clearable filterable>
                <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="导出格式">
              <el-radio-group v-model="exportForm.format">
                <el-radio value="json">JSON</el-radio>
                <el-radio value="xlsx">Excel</el-radio>
                <el-radio value="docx">DOCX</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <div v-if="exportForm.format === 'docx'" style="margin-bottom:16px; color:#909399; font-size:13px">
          DOCX 会导出当前筛选后的条目数据。
        </div>

        <el-divider>筛选条件</el-divider>
        <div v-for="(filter, idx) in exportForm.filters" :key="idx" style="display:flex; gap:12px; margin-bottom:12px; align-items:center; flex-wrap:wrap">
          <el-select v-model="filter.field" placeholder="字段" style="width:200px">
            <el-option v-for="f in filterFields" :key="f" :label="f" :value="f" />
          </el-select>
          <el-select v-model="filter.op" placeholder="操作" style="width:120px">
            <el-option label="等于" value="eq" />
            <el-option label="不等于" value="ne" />
            <el-option label="包含" value="contains" />
            <el-option label="大于" value="gt" />
            <el-option label="小于" value="lt" />
          </el-select>
          <el-input v-model="filter.value" placeholder="值" style="width:200px" />
          <el-button type="danger" circle size="small" @click="exportForm.filters.splice(idx, 1)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-button size="small" @click="exportForm.filters.push({ field: '', op: 'eq', value: '' })">
          <el-icon><Plus /></el-icon> 添加筛选条件
        </el-button>

        <div style="margin-top:24px; display:flex; gap:12px">
          <el-button type="primary" @click="doPreview" :loading="previewing">预览</el-button>
          <el-button type="success" @click="doExport" :loading="exporting">
            <el-icon><Download /></el-icon> 导出
          </el-button>
        </div>
      </el-form>

      <!-- Preview Table -->
      <div v-if="previewData.length" style="margin-top:24px">
        <h3 style="margin-bottom:12px">预览 (共 {{ previewData.length }} 条)</h3>
        <el-table :data="previewData" stripe size="small" max-height="400">
          <el-table-column v-for="col in previewColumns" :key="col"
            :prop="col" :label="col" show-overflow-tooltip min-width="120" />
        </el-table>
      </div>
    </div>

    <div class="card-container">
      <h3 style="margin-bottom:16px">简历导出</h3>
      <el-form :model="resumeExportForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="人员">
              <el-select v-model="resumeExportForm.person_id" placeholder="选择人员" filterable>
                <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="导出格式">
              <el-radio-group v-model="resumeExportForm.format">
                <el-radio value="docx">DOCX</el-radio>
                <el-radio value="pdf">PDF</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <div style="color:#909399; font-size:13px; margin-bottom:16px">
          简历导出会导出该人员全部已通过审核的内容，章节标题使用二级标题，正文使用统一格式生成。
        </div>
        <el-button type="success" @click="doResumeExport" :loading="resumeExporting">
          <el-icon><Download /></el-icon> 导出简历
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const persons = ref([])
const filterFields = ref([])
const previewData = ref([])
const previewColumns = ref([])
const previewing = ref(false)
const exporting = ref(false)
const resumeExporting = ref(false)

const entityTypes = [
  { key: 'papers', label: '论文' },
  { key: 'projects', label: '项目' },
  { key: 'awards', label: '获奖' },
  { key: 'patents', label: '专利' },
  { key: 'software_copyrights', label: '软著' },
  { key: 'student_awards', label: '指导学生获奖' },
  { key: 'conferences', label: '承办会议' },
  { key: 'special_issues', label: '承办特刊' },
  { key: 'academic_roles', label: '学术兼职' },
  { key: 'academic_reports', label: '学术报告' },
  { key: 'teaching_platforms', label: '教学平台建设' },
  { key: 'industry_standards', label: '行业标准' },
]

const exportForm = ref({
  entity_type: 'papers',
  person_id: null,
  format: 'json',
  filters: [],
})

const resumeExportForm = ref({
  person_id: null,
  format: 'docx',
})

async function loadPersons() {
  const res = await api.get('/api/persons/')
  persons.value = res.data
}

async function loadFilterFields() {
  if (!exportForm.value.entity_type) return
  try {
    const res = await api.get(`/api/${exportForm.value.entity_type}/filter-fields`)
    filterFields.value = res.data
  } catch (e) {
    filterFields.value = []
  }
}

async function doPreview() {
  if (exportForm.value.format === 'docx') return
  previewing.value = true
  try {
    const res = await api.post('/api/export/items', {
      ...exportForm.value,
      format: 'json',
    })
    previewData.value = res.data.data
    previewColumns.value = res.data.columns
  } finally {
    previewing.value = false
  }
}

async function doExport() {
  if (exportForm.value.format === 'docx') {
    if (!exportForm.value.entity_type) {
      ElMessage.warning('请先选择数据类型')
      return
    }
    exporting.value = true
    try {
      const res = await api.post('/api/export/items', exportForm.value, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = getFilenameFromHeaders(res.headers['content-disposition']) || 'showcase_export.docx'
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('DOCX导出成功')
    } finally {
      exporting.value = false
    }
  } else if (exportForm.value.format === 'json') {
    await doPreview()
    // Download as JSON file
    const blob = new Blob([JSON.stringify(previewData.value, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${exportForm.value.entity_type}_export.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } else {
    exporting.value = true
    try {
      const res = await api.post('/api/export/items', exportForm.value, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = getFilenameFromHeaders(res.headers['content-disposition']) || `${exportForm.value.entity_type}_export.xlsx`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    } finally {
      exporting.value = false
    }
  }
}

async function doResumeExport() {
  if (!resumeExportForm.value.person_id) {
    ElMessage.warning('请先选择人员')
    return
  }
  resumeExporting.value = true
  try {
    const res = await api.post('/api/export/items', {
      entity_type: null,
      person_id: resumeExportForm.value.person_id,
      format: resumeExportForm.value.format,
      filters: [],
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = getFilenameFromHeaders(res.headers['content-disposition']) || `resume_export.${resumeExportForm.value.format}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('简历导出成功')
  } finally {
    resumeExporting.value = false
  }
}

function getFilenameFromHeaders(contentDisposition) {
  if (!contentDisposition) return ''
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch (e) {}
  }
  const plainMatch = contentDisposition.match(/filename=([^;]+)/i)
  return plainMatch?.[1]?.replace(/"/g, '') || ''
}

onMounted(() => {
  loadPersons()
  loadFilterFields()
})
</script>
