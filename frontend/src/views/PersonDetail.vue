<template>
  <div>
    <div class="page-header">
      <div style="display:flex; align-items:center; gap:12px">
        <el-button @click="$router.push('/persons')" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h2>{{ person?.name || '人员详情' }}</h2>
      </div>
      <div>
        <el-button type="success" @click="$router.push(`/upload/${person?.id}`)">
          <el-icon><Upload /></el-icon> 上传简历
        </el-button>
        <el-button @click="showHistory = true">
          <el-icon><Clock /></el-icon> 历史版本
        </el-button>
      </div>
    </div>

    <!-- Profile Card -->
    <div class="card-container" style="margin-bottom:20px" v-if="profile">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">
        <h3>个人简介</h3>
        <el-button size="small" @click="openProfileDialog">编辑简介</el-button>
      </div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="联系电话">{{ profile.phone }}</el-descriptions-item>
        <el-descriptions-item label="电子邮箱">{{ profile.email }}</el-descriptions-item>
        <el-descriptions-item label="联系地址" :span="2">{{ profile.address }}</el-descriptions-item>
        <el-descriptions-item label="个人介绍" :span="2">
          <div style="white-space:pre-wrap">{{ profile.introduction }}</div>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="educations.length" style="margin-top:16px">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
          <h4>学习经历</h4>
          <el-button size="small" type="primary" @click="openEducationDialog()">新增学习经历</el-button>
        </div>
        <el-table :data="educations" stripe size="small">
          <el-table-column prop="start_date" label="起始" width="120" />
          <el-table-column prop="end_date" label="结束" width="120" />
          <el-table-column prop="school" label="学校" />
          <el-table-column prop="major" label="专业" />
          <el-table-column prop="degree" label="学历/学位" width="120" />
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button size="small" @click="openEducationDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteEducation(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else style="margin-top:16px">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
          <h4>学习经历</h4>
          <el-button size="small" type="primary" @click="openEducationDialog()">新增学习经历</el-button>
        </div>
      </div>

      <div v-if="workExps.length" style="margin-top:16px">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
          <h4>工作经历</h4>
          <el-button size="small" type="primary" @click="openWorkDialog()">新增工作经历</el-button>
        </div>
        <el-table :data="workExps" stripe size="small">
          <el-table-column prop="start_date" label="起始" width="120" />
          <el-table-column prop="end_date" label="结束" width="120" />
          <el-table-column prop="organization" label="单位" />
          <el-table-column prop="position" label="职位" />
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button size="small" @click="openWorkDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteWork(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else style="margin-top:16px">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
          <h4>工作经历</h4>
          <el-button size="small" type="primary" @click="openWorkDialog()">新增工作经历</el-button>
        </div>
      </div>
    </div>

    <!-- Entity Tabs -->
    <div class="card-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane v-for="tab in tabs" :key="tab.key" :label="tab.label" :name="tab.key">
          <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center">
            <span style="color:#909399; font-size:13px">
              共 {{ getFilteredTabRows(tab).length }} / {{ tabData[tab.key]?.length || 0 }} 条
            </span>
            <el-button size="small" type="primary" @click="openAddDialog(tab)">
              <el-icon><Plus /></el-icon> 新增
            </el-button>
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
          <el-table :data="getFilteredTabRows(tab)" stripe size="small" max-height="500">
            <el-table-column v-for="col in tab.columns" :key="col.prop"
              :prop="col.prop" :label="col.label" :width="col.width"
              :show-overflow-tooltip="true">
              <template #default="{ row }" v-if="col.prop === 'authors'">
                <span v-if="Array.isArray(row.authors)">
                  {{ row.authors.map(a => a.name + (a.is_corresponding_author ? '*' : '')).join(', ') }}
                </span>
              </template>
              <template #default="{ row }" v-else-if="col.prop === 'is_first_author' || col.prop === 'is_corresponding_author'">
                <el-tag size="small" :type="row[col.prop] ? 'success' : 'info'">
                  {{ row[col.prop] ? '是' : '否' }}
                </el-tag>
              </template>
              <template #default="{ row }" v-else-if="col.prop === 'applicants'">
                <span v-if="Array.isArray(row.applicants)">
                  {{ row.applicants.map(a => a.name).join(', ') }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="90" v-if="tab.hasConfidence">
              <template #default="{ row }">
                <el-tag size="small" :type="confidenceType(row.confidence)">
                  {{ (row.confidence * 100).toFixed(0) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" v-if="tab.hasConfidence">
              <template #default="{ row }">
                <el-tag size="small"
                  :type="row.review_status === 'approved' ? 'success' : row.review_status === 'rejected' ? 'danger' : 'warning'">
                  {{ statusLabel(row.review_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="附件" width="70">
              <template #default="{ row }">
                <el-button size="small" circle @click="openAttachments(tab.key, row.id)">
                  <el-icon><Paperclip /></el-icon>
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEditDialog(tab, row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteItem(tab.key, row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Resume History Dialog -->
    <el-dialog v-model="showHistory" title="简历历史版本" width="600px">
      <el-table :data="resumeHistory" stripe>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column prop="uploaded_at" label="上传时间" width="180">
          <template #default="{ row }">{{ formatDate(row.uploaded_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="downloadResume(row.id)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Edit/Add Dialog -->
    <el-dialog v-model="showEditDialog" :title="editMode === 'add' ? '新增' : '编辑'" width="600px">
      <el-form :model="editForm" label-width="100px" label-position="top">
        <el-form-item v-for="col in currentEditCols" :key="col.prop" :label="col.label">
          <el-input v-model="editForm[col.prop]" :placeholder="col.label"
            :type="col.type === 'textarea' ? 'textarea' : 'text'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- Attachments Dialog -->
    <el-dialog v-model="showAttachDialog" title="附件管理" width="600px">
      <el-upload
        :action="`/api/attachments/upload?entity_type=${attachEntity.type}&entity_id=${attachEntity.id}`"
        :headers="{ Authorization: `Bearer ${auth.token}` }"
        @success="loadAttachments"
        :on-success="loadAttachments"
      >
        <el-button type="primary" size="small"><el-icon><Upload /></el-icon> 上传附件</el-button>
      </el-upload>
      <el-table :data="attachments" stripe size="small" style="margin-top:12px">
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column prop="uploaded_at" label="上传时间" width="180">
          <template #default="{ row }">{{ formatDate(row.uploaded_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="downloadAttachment(row.id)">下载</el-button>
            <el-button size="small" type="danger" @click="deleteAttachment(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="showProfileDialog" title="编辑个人简介" width="700px">
      <el-form :model="profileForm" label-position="top">
        <el-form-item label="联系电话">
          <el-input v-model="profileForm.phone" />
        </el-form-item>
        <el-form-item label="电子邮箱">
          <el-input v-model="profileForm.email" />
        </el-form-item>
        <el-form-item label="联系地址">
          <el-input v-model="profileForm.address" />
        </el-form-item>
        <el-form-item label="个人介绍">
          <el-input v-model="profileForm.introduction" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProfileDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProfile" :loading="savingProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEducationDialog" :title="educationEditId ? '编辑学习经历' : '新增学习经历'" width="600px">
      <el-form :model="educationForm" label-position="top">
        <el-form-item label="开始时间"><el-input v-model="educationForm.start_date" /></el-form-item>
        <el-form-item label="结束时间"><el-input v-model="educationForm.end_date" /></el-form-item>
        <el-form-item label="学校"><el-input v-model="educationForm.school" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="educationForm.major" /></el-form-item>
        <el-form-item label="学历/学位"><el-input v-model="educationForm.degree" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEducationDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEducation" :loading="savingEducation">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showWorkDialog" :title="workEditId ? '编辑工作经历' : '新增工作经历'" width="600px">
      <el-form :model="workForm" label-position="top">
        <el-form-item label="开始时间"><el-input v-model="workForm.start_date" /></el-form-item>
        <el-form-item label="结束时间"><el-input v-model="workForm.end_date" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="workForm.organization" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="workForm.position" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWorkDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWork" :loading="savingWork">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useListFilters } from '../composables/useListFilters'

const route = useRoute()
const auth = useAuthStore()
const personId = computed(() => route.params.id)

const person = ref(null)
const profile = ref(null)
const educations = ref([])
const workExps = ref([])
const resumeHistory = ref([])
const tabData = ref({})
const activeTab = ref('papers')
const showHistory = ref(false)
const showEditDialog = ref(false)
const showAttachDialog = ref(false)
const showProfileDialog = ref(false)
const showEducationDialog = ref(false)
const showWorkDialog = ref(false)
const editMode = ref('add')
const editForm = ref({})
const currentEditCols = ref([])
const currentEditTab = ref(null)
const currentEditId = ref(null)
const saving = ref(false)
const savingProfile = ref(false)
const savingEducation = ref(false)
const savingWork = ref(false)
const attachEntity = ref({ type: '', id: 0 })
const attachments = ref([])
const profileForm = ref({ introduction: '', phone: '', email: '', address: '' })
const educationForm = ref({ start_date: '', end_date: '', school: '', major: '', degree: '' })
const workForm = ref({ start_date: '', end_date: '', organization: '', position: '' })
const educationEditId = ref(null)
const workEditId = ref(null)
const {
  ensureFilterState,
  resetFilterState,
  addFilter,
  removeFilter,
  getFilterableColumns,
  getFilteredRows,
} = useListFilters()

const tabs = [
  { key: 'papers', label: '论文', hasConfidence: true, apiName: 'papers',
    columns: [
      { prop: 'authors', label: '作者', width: 200 },
      { prop: 'title', label: '标题' },
      { prop: 'journal', label: '期刊', width: 180 },
      { prop: 'year', label: '年份', width: 70 },
      { prop: 'is_first_author', label: '第一作者', width: 90 },
      { prop: 'is_corresponding_author', label: '通讯作者', width: 90 },
      { prop: 'doi', label: 'DOI', width: 150 },
    ],
    editCols: [
      { prop: 'authors_text', label: '作者' },
      { prop: 'title', label: '标题' },
      { prop: 'journal', label: '期刊' },
      { prop: 'year', label: '年份' },
      { prop: 'doi', label: 'DOI' },
      { prop: 'volume', label: '卷号' },
      { prop: 'issue', label: '期号' },
      { prop: 'pages', label: '页数' },
    ]
  },
  { key: 'projects', label: '项目', hasConfidence: true, apiName: 'projects',
    columns: [
      { prop: 'project_type', label: '类型', width: 150 },
      { prop: 'name', label: '名称' },
      { prop: 'project_number', label: '编号', width: 140 },
      { prop: 'start_date', label: '开始', width: 100 },
      { prop: 'end_date', label: '结束', width: 100 },
      { prop: 'role', label: '身份', width: 100 },
      { prop: 'amount', label: '金额', width: 80 },
    ],
    editCols: [
      { prop: 'project_type', label: '项目类型' },
      { prop: 'name', label: '项目名称' },
      { prop: 'project_number', label: '项目编号' },
      { prop: 'start_date', label: '开始日期' },
      { prop: 'end_date', label: '结束日期' },
      { prop: 'role', label: '当前身份' },
      { prop: 'amount', label: '项目金额' },
    ]
  },
  { key: 'awards', label: '获奖', hasConfidence: true, apiName: 'awards',
    columns: [
      { prop: 'award_name', label: '奖项名称' },
      { prop: 'project_name', label: '项目名称' },
      { prop: 'participants', label: '人员', width: 200 },
      { prop: 'awarding_body', label: '颁奖单位', width: 150 },
    ],
    editCols: [
      { prop: 'award_name', label: '奖项名称' },
      { prop: 'project_name', label: '项目名称' },
      { prop: 'participants', label: '人员' },
      { prop: 'awarding_body', label: '颁奖单位' },
    ]
  },
  { key: 'patents', label: '专利', hasConfidence: true, apiName: 'patents',
    columns: [
      { prop: 'applicants', label: '申请人', width: 200 },
      { prop: 'patent_name', label: '专利名称' },
      { prop: 'application_number', label: '申请号', width: 180 },
      { prop: 'authorization_number', label: '授权号', width: 180 },
      { prop: 'status', label: '状态', width: 80 },
    ],
    editCols: [
      { prop: 'patent_name', label: '专利名称' },
      { prop: 'application_number', label: '申请号' },
      { prop: 'authorization_number', label: '授权号' },
      { prop: 'status', label: '状态' },
    ]
  },
  { key: 'software_copyrights', label: '软著', hasConfidence: true, apiName: 'software_copyrights',
    columns: [
      { prop: 'applicant', label: '申请人', width: 200 },
      { prop: 'name', label: '软著名称' },
      { prop: 'registration_date', label: '登记时间', width: 140 },
      { prop: 'registration_number', label: '登记号', width: 160 },
    ],
    editCols: [
      { prop: 'applicant', label: '申请人' },
      { prop: 'name', label: '软著名称' },
      { prop: 'registration_date', label: '登记时间' },
      { prop: 'registration_number', label: '登记号' },
    ]
  },
  { key: 'student_awards', label: '指导学生获奖', hasConfidence: true, apiName: 'student_awards',
    columns: [
      { prop: 'award_name', label: '奖项名称' },
      { prop: 'level', label: '等级', width: 100 },
      { prop: 'role', label: '身份', width: 100 },
      { prop: 'award_date', label: '获奖时间', width: 120 },
    ],
    editCols: [
      { prop: 'award_name', label: '奖项名称' },
      { prop: 'level', label: '奖项等级' },
      { prop: 'role', label: '身份' },
      { prop: 'award_date', label: '获奖时间' },
    ]
  },
  { key: 'conferences', label: '承办会议', hasConfidence: true, apiName: 'conferences',
    columns: [
      { prop: 'name', label: '会议名称' },
      { prop: 'date', label: '时间', width: 120 },
      { prop: 'role', label: '身份', width: 100 },
      { prop: 'website', label: '网址', width: 200 },
    ],
    editCols: [
      { prop: 'name', label: '会议名称' },
      { prop: 'date', label: '会议时间' },
      { prop: 'role', label: '身份' },
      { prop: 'website', label: '会议网址' },
    ]
  },
  { key: 'special_issues', label: '承办特刊', hasConfidence: true, apiName: 'special_issues',
    columns: [
      { prop: 'issue_name', label: '特刊名称' },
      { prop: 'journal_name', label: '期刊名称', width: 180 },
      { prop: 'date', label: '时间', width: 120 },
      { prop: 'role', label: '身份', width: 120 },
    ],
    editCols: [
      { prop: 'issue_name', label: '特刊名称' },
      { prop: 'journal_name', label: '期刊名称' },
      { prop: 'date', label: '特刊时间' },
      { prop: 'role', label: '身份' },
    ]
  },
  { key: 'academic_roles', label: '学术兼职', hasConfidence: true, apiName: 'academic_roles',
    columns: [
      { prop: 'title', label: '头衔' },
      { prop: 'start_date', label: '开始', width: 120 },
      { prop: 'end_date', label: '结束', width: 120 },
    ],
    editCols: [
      { prop: 'title', label: '头衔' },
      { prop: 'start_date', label: '开始时间' },
      { prop: 'end_date', label: '结束时间' },
    ]
  },
  { key: 'academic_reports', label: '学术报告', hasConfidence: true, apiName: 'academic_reports',
    columns: [
      { prop: 'name', label: '报告名称' },
      { prop: 'report_type', label: '类型', width: 120 },
      { prop: 'date', label: '时间', width: 120 },
    ],
    editCols: [
      { prop: 'name', label: '报告名称' },
      { prop: 'report_type', label: '报告类型' },
      { prop: 'date', label: '报告时间' },
    ]
  },
  { key: 'teaching_platforms', label: '教学平台', hasConfidence: true, apiName: 'teaching_platforms',
    columns: [
      { prop: 'name', label: '名称' },
      { prop: 'issuing_body', label: '发布单位', width: 150 },
      { prop: 'approval_date', label: '获批时间', width: 120 },
      { prop: 'position', label: '职位', width: 100 },
    ],
    editCols: [
      { prop: 'name', label: '名称' },
      { prop: 'issuing_body', label: '发布单位' },
      { prop: 'approval_date', label: '获批时间' },
      { prop: 'position', label: '担任职位' },
    ]
  },
  { key: 'industry_standards', label: '行业标准', hasConfidence: true, apiName: 'industry_standards',
    columns: [
      { prop: 'name', label: '标准名称' },
      { prop: 'publish_date', label: '发布时间', width: 120 },
      { prop: 'role', label: '身份', width: 100 },
    ],
    editCols: [
      { prop: 'name', label: '标准名称' },
      { prop: 'publish_date', label: '发布时间' },
      { prop: 'role', label: '身份' },
    ]
  },
]

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

function confidenceType(c) {
  if (c >= 0.8) return 'success'
  if (c >= 0.5) return 'warning'
  return 'danger'
}

function statusLabel(s) {
  return { pending: '待审', approved: '通过', rejected: '拒绝' }[s] || s
}

function getFilteredTabRows(tab) {
  return getFilteredRows(tab, tabData.value[tab.key] || [])
}

async function loadPerson() {
  const res = await api.get(`/api/persons/${personId.value}`)
  person.value = res.data
}

async function loadProfile() {
  try {
    const [profRes, eduRes, workRes] = await Promise.all([
      api.get(`/api/profile/${personId.value}`),
      api.get(`/api/profile/${personId.value}/educations`),
      api.get(`/api/profile/${personId.value}/work-experiences`),
    ])
    profile.value = profRes.data
    profileForm.value = {
      introduction: profRes.data.introduction || '',
      phone: profRes.data.phone || '',
      email: profRes.data.email || '',
      address: profRes.data.address || '',
    }
    educations.value = eduRes.data
    workExps.value = workRes.data
  } catch (e) {}
}

function openProfileDialog() {
  profileForm.value = {
    introduction: profile.value?.introduction || '',
    phone: profile.value?.phone || '',
    email: profile.value?.email || '',
    address: profile.value?.address || '',
  }
  showProfileDialog.value = true
}

async function saveProfile() {
  savingProfile.value = true
  try {
    await api.put(`/api/profile/${personId.value}`, profileForm.value)
    ElMessage.success('个人简介已更新')
    showProfileDialog.value = false
    await loadProfile()
  } finally {
    savingProfile.value = false
  }
}

function openEducationDialog(row = null) {
  educationEditId.value = row?.id || null
  educationForm.value = row ? {
    start_date: row.start_date || '',
    end_date: row.end_date || '',
    school: row.school || '',
    major: row.major || '',
    degree: row.degree || '',
  } : { start_date: '', end_date: '', school: '', major: '', degree: '' }
  showEducationDialog.value = true
}

async function saveEducation() {
  savingEducation.value = true
  try {
    if (educationEditId.value) {
      await api.put(`/api/profile/educations/${educationEditId.value}`, educationForm.value)
    } else {
      await api.post(`/api/profile/${personId.value}/educations`, {
        ...educationForm.value,
        person_id: parseInt(personId.value)
      })
    }
    ElMessage.success('学习经历已保存')
    showEducationDialog.value = false
    await loadProfile()
  } finally {
    savingEducation.value = false
  }
}

async function deleteEducation(id) {
  try {
    await ElMessageBox.confirm('确定删除这条学习经历吗？', '确认删除', { type: 'warning' })
    await api.delete(`/api/profile/educations/${id}`)
    ElMessage.success('删除成功')
    await loadProfile()
  } catch (e) {}
}

function openWorkDialog(row = null) {
  workEditId.value = row?.id || null
  workForm.value = row ? {
    start_date: row.start_date || '',
    end_date: row.end_date || '',
    organization: row.organization || '',
    position: row.position || '',
  } : { start_date: '', end_date: '', organization: '', position: '' }
  showWorkDialog.value = true
}

async function saveWork() {
  savingWork.value = true
  try {
    if (workEditId.value) {
      await api.put(`/api/profile/work-experiences/${workEditId.value}`, workForm.value)
    } else {
      await api.post(`/api/profile/${personId.value}/work-experiences`, {
        ...workForm.value,
        person_id: parseInt(personId.value)
      })
    }
    ElMessage.success('工作经历已保存')
    showWorkDialog.value = false
    await loadProfile()
  } finally {
    savingWork.value = false
  }
}

async function deleteWork(id) {
  try {
    await ElMessageBox.confirm('确定删除这条工作经历吗？', '确认删除', { type: 'warning' })
    await api.delete(`/api/profile/work-experiences/${id}`)
    ElMessage.success('删除成功')
    await loadProfile()
  } catch (e) {}
}

async function loadTabData(tabKey) {
  try {
    const res = await api.get(`/api/${tabKey}/`, { params: { person_id: personId.value } })
    tabData.value[tabKey] = res.data
  } catch (e) {
    tabData.value[tabKey] = []
  }
}

async function loadAllTabs() {
  await Promise.all(tabs.map(tab => loadTabData(tab.key)))
}

async function loadResumeHistory() {
  try {
    const res = await api.get(`/api/resumes/${personId.value}/history`)
    resumeHistory.value = res.data
  } catch (e) {}
}

function downloadResume(id) {
  window.open(`/api/resumes/download/${id}`, '_blank')
}

function openAddDialog(tab) {
  editMode.value = 'add'
  currentEditTab.value = tab
  currentEditCols.value = tab.editCols
  editForm.value = {}
  tab.editCols.forEach(c => editForm.value[c.prop] = '')
  showEditDialog.value = true
}

function openEditDialog(tab, row) {
  editMode.value = 'edit'
  currentEditTab.value = tab
  currentEditCols.value = tab.editCols
  currentEditId.value = row.id
  editForm.value = {}
  tab.editCols.forEach(c => {
    if (c.prop === 'authors_text') {
      editForm.value[c.prop] = Array.isArray(row.authors)
        ? row.authors.map(a => a.name + (a.is_corresponding_author ? '*' : '')).join(', ')
        : ''
    } else {
      editForm.value[c.prop] = row[c.prop] || ''
    }
  })
  showEditDialog.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    const payload = { ...editForm.value }
    if (currentEditTab.value.key === 'papers' && payload.authors_text !== undefined) {
      payload.authors = payload.authors_text
        .split(',')
        .map(s => s.trim())
        .filter(Boolean)
        .map((name, index) => ({
          name: name.replace(/\*/g, '').trim(),
          order: index,
          is_first_author: index === 0,
          is_corresponding_author: name.includes('*'),
        }))
      delete payload.authors_text
    }
    if (editMode.value === 'add') {
      await api.post(`/api/${currentEditTab.value.key}/`, {
        ...payload,
        person_id: parseInt(personId.value)
      })
      ElMessage.success('新增成功')
    } else {
      await api.put(`/api/${currentEditTab.value.key}/${currentEditId.value}`, payload)
      ElMessage.success('更新成功')
    }
    showEditDialog.value = false
    await loadTabData(currentEditTab.value.key)
  } finally {
    saving.value = false
  }
}

async function deleteItem(tabKey, itemId) {
  try {
    await ElMessageBox.confirm('确定删除此条目吗？', '确认删除', { type: 'warning' })
    await api.delete(`/api/${tabKey}/${itemId}`)
    ElMessage.success('删除成功')
    await loadTabData(tabKey)
  } catch (e) {}
}

function openAttachments(entityType, entityId) {
  attachEntity.value = { type: entityType, id: entityId }
  loadAttachments()
  showAttachDialog.value = true
}

async function loadAttachments() {
  try {
    const res = await api.get('/api/attachments/', {
      params: { entity_type: attachEntity.value.type, entity_id: attachEntity.value.id }
    })
    attachments.value = res.data
  } catch (e) {
    attachments.value = []
  }
}

function downloadAttachment(id) {
  window.open(`/api/attachments/download/${id}`, '_blank')
}

async function deleteAttachment(id) {
  try {
    await ElMessageBox.confirm('确定删除此附件吗？', '确认删除', { type: 'warning' })
    await api.delete(`/api/attachments/${id}`)
    ElMessage.success('删除成功')
    await loadAttachments()
  } catch (e) {}
}

onMounted(async () => {
  await loadPerson()
  await Promise.all([loadProfile(), loadAllTabs(), loadResumeHistory()])
})
</script>
