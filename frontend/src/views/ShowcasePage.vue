<template>
  <div class="showcase-page">
    <div class="page-header showcase-header">
      <div>
        <h2>{{ person?.name || '成果展示' }}</h2>
        <div v-if="person?.name_en" class="showcase-subtitle">{{ person.name_en }}</div>
      </div>
      <el-select v-model="selectedPersonId" filterable placeholder="选择人员" style="width:240px" @change="handlePersonChange">
        <el-option v-for="item in persons" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
    </div>

    <div class="card-container" v-if="profile">
      <h3 style="margin-bottom:16px">个人简介</h3>
      <el-descriptions :column="mobile ? 1 : 2" border>
        <el-descriptions-item label="联系电话">{{ profile.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电子邮箱">{{ profile.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系地址" :span="mobile ? 1 : 2">{{ profile.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="个人介绍" :span="mobile ? 1 : 2">
          <div class="showcase-intro">{{ profile.introduction || '-' }}</div>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="educations.length" style="margin-top:16px">
        <h4 style="margin-bottom:8px">学习经历</h4>
        <div class="table-scroll">
          <el-table :data="educations" stripe size="small">
            <el-table-column prop="start_date" label="起始" width="120" />
            <el-table-column prop="end_date" label="结束" width="120" />
            <el-table-column prop="school" label="学校" min-width="180" />
            <el-table-column prop="major" label="专业" min-width="160" />
            <el-table-column prop="degree" label="学历/学位" min-width="120" />
          </el-table>
        </div>
      </div>

      <div v-if="workExperiences.length" style="margin-top:16px">
        <h4 style="margin-bottom:8px">工作经历</h4>
        <div class="table-scroll">
          <el-table :data="workExperiences" stripe size="small">
            <el-table-column prop="start_date" label="起始" width="120" />
            <el-table-column prop="end_date" label="结束" width="120" />
            <el-table-column prop="organization" label="单位" min-width="180" />
            <el-table-column prop="position" label="职位" min-width="180" />
          </el-table>
        </div>
      </div>
    </div>

    <div class="card-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane v-for="tab in tabs" :key="tab.key" :label="tab.label" :name="tab.key">
          <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center">
            <span style="color:#909399; font-size:13px">
              共 {{ getFilteredTabRows(tab).length }} / {{ (items[tab.key] || []).length }} 条
            </span>
          </div>
          <div style="margin-bottom:12px; display:grid; gap:10px">
            <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap">
              <el-input
                v-model="ensureFilterState(tab.key).keyword"
                placeholder="搜索当前列表"
                clearable
                style="width:260px"
              />
              <el-button size="small" @click="addFilter(tab.key)">添加筛选条件</el-button>
              <el-button size="small" text @click="resetFilterState(tab.key)">清空筛选</el-button>
            </div>
            <div
              v-for="(filter, idx) in ensureFilterState(tab.key).filters"
              :key="`${tab.key}-${idx}`"
              style="display:flex; gap:12px; align-items:center; flex-wrap:wrap"
            >
              <el-select v-model="filter.field" placeholder="字段" style="width:180px">
                <el-option
                  v-for="field in getFilterableColumns(tab)"
                  :key="field.prop"
                  :label="field.label"
                  :value="field.prop"
                />
              </el-select>
              <el-select v-model="filter.op" placeholder="条件" style="width:120px">
                <el-option label="包含" value="contains" />
                <el-option label="等于" value="eq" />
                <el-option label="不等于" value="ne" />
              </el-select>
              <el-input v-model="filter.value" placeholder="值" style="width:220px" />
              <el-button size="small" type="danger" @click="removeFilter(tab.key, idx)">删除</el-button>
            </div>
          </div>
          <div class="table-scroll">
            <el-table :data="getFilteredTabRows(tab)" stripe size="small" max-height="520">
              <el-table-column v-for="col in tab.columns" :key="col.prop"
                :prop="col.prop" :label="col.label" :width="col.width" :min-width="col.minWidth"
                :show-overflow-tooltip="true">
                <template #default="{ row }" v-if="col.prop === 'authors'">
                  <span v-if="Array.isArray(row.authors)">
                    {{ row.authors.map(a => a.name + (a.is_corresponding_author ? '*' : '')).join(', ') }}
                  </span>
                </template>
                <template #default="{ row }" v-else-if="col.prop === 'applicants'">
                  <span v-if="Array.isArray(row.applicants)">
                    {{ row.applicants.map(a => a.name).join(', ') }}
                  </span>
                </template>
                <template #default="{ row }" v-else-if="col.prop === 'is_first_author' || col.prop === 'is_corresponding_author'">
                  <el-tag size="small" :type="row[col.prop] ? 'success' : 'info'">
                    {{ row[col.prop] ? '是' : '否' }}
                  </el-tag>
                </template>
                <template #default="{ row }" v-else-if="col.prop === 'attachments'">
                  <div class="attachment-list">
                    <el-button
                      v-for="attachment in row.attachments || []"
                      :key="attachment.id"
                      size="small"
                      @click="downloadAttachment(attachment.id)"
                    >
                      {{ attachment.original_filename }}
                    </el-button>
                    <span v-if="!(row.attachments || []).length" style="color:#909399">-</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="card-container" v-if="loaded && !hasContent">
      <el-empty description="暂无可展示的已通过条目" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useListFilters } from '../composables/useListFilters'

const route = useRoute()
const router = useRouter()

const persons = ref([])
const selectedPersonId = ref(null)
const person = ref(null)
const profile = ref(null)
const educations = ref([])
const workExperiences = ref([])
const items = ref({})
const loaded = ref(false)
const mobile = ref(window.innerWidth <= 768)
const activeTab = ref('papers')
const {
  ensureFilterState,
  resetFilterState,
  addFilter,
  removeFilter,
  getFilterableColumns,
  getFilteredRows,
} = useListFilters()

const tabs = [
  { key: 'papers', label: '论文', columns: [
    { prop: 'authors', label: '作者', minWidth: 220 },
    { prop: 'title', label: '标题', minWidth: 260 },
    { prop: 'journal', label: '期刊', minWidth: 180 },
    { prop: 'year', label: '年份', width: 90 },
    { prop: 'is_first_author', label: '第一作者', width: 100 },
    { prop: 'is_corresponding_author', label: '通讯作者', width: 100 },
    { prop: 'doi', label: 'DOI', minWidth: 220 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'projects', label: '项目', columns: [
    { prop: 'project_type', label: '类型', minWidth: 160 },
    { prop: 'name', label: '名称', minWidth: 240 },
    { prop: 'project_number', label: '编号', minWidth: 160 },
    { prop: 'start_date', label: '开始', width: 110 },
    { prop: 'end_date', label: '结束', width: 110 },
    { prop: 'role', label: '身份', minWidth: 120 },
    { prop: 'amount', label: '金额', width: 110 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'awards', label: '获奖', columns: [
    { prop: 'award_name', label: '奖项名称', minWidth: 220 },
    { prop: 'project_name', label: '项目名称', minWidth: 220 },
    { prop: 'participants', label: '人员', minWidth: 220 },
    { prop: 'awarding_body', label: '颁奖单位', minWidth: 180 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'patents', label: '专利', columns: [
    { prop: 'applicants', label: '申请人', minWidth: 220 },
    { prop: 'patent_name', label: '专利名称', minWidth: 260 },
    { prop: 'application_number', label: '申请号', minWidth: 180 },
    { prop: 'authorization_number', label: '授权号', minWidth: 180 },
    { prop: 'status', label: '状态', width: 90 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'software_copyrights', label: '软著', columns: [
    { prop: 'applicant', label: '申请人', minWidth: 180 },
    { prop: 'name', label: '软著名称', minWidth: 220 },
    { prop: 'registration_date', label: '登记时间', minWidth: 140 },
    { prop: 'registration_number', label: '登记号', minWidth: 180 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'student_awards', label: '指导学生获奖', columns: [
    { prop: 'award_name', label: '奖项名称', minWidth: 220 },
    { prop: 'level', label: '等级', minWidth: 120 },
    { prop: 'role', label: '身份', minWidth: 120 },
    { prop: 'award_date', label: '获奖时间', minWidth: 140 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'conferences', label: '承办会议', columns: [
    { prop: 'name', label: '会议名称', minWidth: 260 },
    { prop: 'date', label: '时间', minWidth: 130 },
    { prop: 'role', label: '身份', minWidth: 120 },
    { prop: 'website', label: '网址', minWidth: 220 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'special_issues', label: '承办特刊', columns: [
    { prop: 'issue_name', label: '特刊名称', minWidth: 240 },
    { prop: 'journal_name', label: '期刊名称', minWidth: 200 },
    { prop: 'date', label: '时间', minWidth: 130 },
    { prop: 'role', label: '身份', minWidth: 120 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'academic_roles', label: '学术兼职', columns: [
    { prop: 'title', label: '头衔', minWidth: 240 },
    { prop: 'start_date', label: '开始', minWidth: 130 },
    { prop: 'end_date', label: '结束', minWidth: 130 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'academic_reports', label: '学术报告', columns: [
    { prop: 'name', label: '报告名称', minWidth: 240 },
    { prop: 'report_type', label: '类型', minWidth: 140 },
    { prop: 'date', label: '时间', minWidth: 140 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'teaching_platforms', label: '教学平台建设', columns: [
    { prop: 'name', label: '名称', minWidth: 220 },
    { prop: 'issuing_body', label: '发布单位', minWidth: 180 },
    { prop: 'approval_date', label: '获批时间', minWidth: 140 },
    { prop: 'position', label: '职位', minWidth: 140 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
  { key: 'industry_standards', label: '行业标准', columns: [
    { prop: 'name', label: '标准名称', minWidth: 240 },
    { prop: 'publish_date', label: '发布时间', minWidth: 140 },
    { prop: 'role', label: '身份', minWidth: 120 },
    { prop: 'attachments', label: '附件', minWidth: 200 },
  ]},
]

const hasContent = computed(() => {
  return !!(
    profile.value?.introduction ||
    educations.value.length ||
    workExperiences.value.length ||
    tabs.some(tab => (items.value[tab.key] || []).length)
  )
})

function getFilteredTabRows(tab) {
  return getFilteredRows(tab, items.value[tab.key] || [])
}

function updateMobile() {
  mobile.value = window.innerWidth <= 768
}

async function loadPersons() {
  const res = await api.get('/api/showcase/persons')
  persons.value = res.data
  if (!selectedPersonId.value && res.data.length) {
    selectedPersonId.value = Number(route.params.id) || res.data[0].id
  }
}

async function loadShowcase(personId) {
  const res = await api.get(`/api/showcase/persons/${personId}`)
  person.value = res.data.person
  profile.value = res.data.profile
  educations.value = res.data.educations
  workExperiences.value = res.data.work_experiences
  items.value = res.data.items
  loaded.value = true
}

function handlePersonChange(personId) {
  router.replace(`/showcase/${personId}`)
  loadShowcase(personId)
}

function downloadAttachment(id) {
  window.open(`/api/showcase/attachments/download/${id}`, '_blank')
}

onMounted(async () => {
  window.addEventListener('resize', updateMobile)
  await loadPersons()
  if (selectedPersonId.value) {
    await loadShowcase(selectedPersonId.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMobile)
})
</script>

<style scoped>
.showcase-page {
  display: grid;
  gap: 20px;
}

.showcase-header {
  align-items: end;
}

.showcase-subtitle {
  margin-top: 6px;
  color: #909399;
  font-size: 14px;
}

.showcase-intro {
  white-space: pre-wrap;
  line-height: 1.8;
}

.table-scroll {
  overflow-x: auto;
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .showcase-header {
    align-items: stretch;
  }
}
</style>
