<template>
  <div>
    <div class="page-header">
      <h2>审核管理</h2>
      <div style="display:flex; gap:12px; align-items:center">
        <el-select v-model="selectedPerson" placeholder="选择人员" filterable style="width:200px"
                   @change="loadPendingItems">
          <el-option v-for="p in persons" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <div style="display:flex; align-items:center; gap:8px">
          <span style="font-size:13px; color:#909399">置信度阈值:</span>
          <el-slider v-model="threshold" :min="0" :max="100" :step="5" style="width:150px"
                     :format-tooltip="v => v + '%'" />
          <span style="font-size:13px; font-weight:600">{{ threshold }}%</span>
        </div>
        <el-button type="success" @click="batchApprove" :disabled="!selectedPerson">
          <el-icon><Checked /></el-icon> 一键审批
        </el-button>
        <div style="display:flex; align-items:center; gap:8px; margin-left:8px">
          <span style="font-size:13px; color:#909399">AI审核阈值:</span>
          <el-slider v-model="aiThreshold" :min="0" :max="100" :step="5" style="width:150px"
                     :format-tooltip="v => v + '%'" />
          <span style="font-size:13px; font-weight:600">{{ aiThreshold }}%</span>
        </div>
        <el-button v-if="!aiReviewing" type="primary" @click="runAiReview" :disabled="!selectedPerson || !aiConfigured">
          <el-icon><MagicStick /></el-icon> AI审核
        </el-button>
        <el-button v-else type="danger" @click="cancelAiReview">
          取消 AI 审核
        </el-button>
      </div>
    </div>

    <div v-if="aiStatusText" class="card-container" style="margin-bottom:16px; padding:14px 18px">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:16px">
        <span style="color:#606266">{{ aiStatusText }}</span>
        <span v-if="aiReviewing" style="color:#409eff; font-size:13px">处理中...</span>
      </div>
    </div>

    <div class="card-container" v-if="selectedPerson">
      <div v-for="(items, entityType) in pendingItems" :key="entityType" style="margin-bottom:24px">
        <h3 style="margin-bottom:12px; text-transform:capitalize">{{ entityLabels[entityType] || entityType }}</h3>
        <el-table :data="items" stripe size="small" row-key="id">
          <el-table-column type="expand" width="56">
            <template #default="{ row: record }">
              <div class="review-expand">
                <div class="review-block">
                  <div class="review-block-title">原始文本</div>
                  <div class="review-raw-text">{{ record.raw_text }}</div>
                </div>
                <div class="review-block">
                  <div class="review-block-header">
                    <span class="review-block-title">结构化信息</span>
                    <el-button link type="primary" @click="resetDraft(entityType, record)">重置编辑</el-button>
                  </div>
                  <el-table :data="getStructuredRows(entityType, record)" size="small" border>
                    <el-table-column prop="label" label="字段" width="180" />
                    <el-table-column label="提取结果">
                      <template #default="{ row: fieldRow }">
                        <el-input v-model="getDraft(entityType, record)[fieldRow.key]" />
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="raw_text" label="原始文本" show-overflow-tooltip min-width="420" />
          <el-table-column label="置信度" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="confidenceType(row.confidence)">
                {{ (row.confidence * 100).toFixed(0) }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="AI状态" width="120">
            <template #default="{ row }">
              <el-tooltip v-if="row.ai_review_message" :content="row.ai_review_message" placement="top">
                <el-tag size="small" :type="aiStatusType(row.ai_review_status)">
                  {{ aiStatusLabel(row.ai_review_status) }}
                </el-tag>
              </el-tooltip>
              <el-tag v-else size="small" :type="aiStatusType(row.ai_review_status)">
                {{ aiStatusLabel(row.ai_review_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row: record }">
              <el-button size="small" type="primary"
                         :loading="aiItemLoading[aiItemKey(entityType, record.id)]"
                         :disabled="!aiConfigured"
                         @click="runSingleAiReview(entityType, record)">
                AI审核
              </el-button>
              <el-button size="small" type="success" @click="reviewItem(entityType, record, 'approve')">
                <el-icon><Check /></el-icon> 通过
              </el-button>
              <el-button size="small" type="danger" @click="reviewItem(entityType, record, 'reject')">
                <el-icon><Close /></el-icon> 拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-if="Object.keys(pendingItems).length === 0" description="暂无待审核条目" />
    </div>
    <div v-else class="card-container">
      <el-empty description="请先选择一个人员" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const persons = ref([])
const selectedPerson = ref(null)
const pendingItems = ref({})
const threshold = ref(80)
const aiThreshold = ref(60)
const editDrafts = ref({})
const aiConfigured = ref(false)
const aiReviewing = ref(false)
const aiReviewCancelled = ref(false)
const aiStatusText = ref('')
const aiItemLoading = ref({})
const aiConcurrency = ref(2)
const aiRetryCount = ref(1)

const entityLabels = {
  papers: '论文', projects: '项目', awards: '获奖', patents: '专利',
  software_copyrights: '软著', student_awards: '指导学生获奖',
  conferences: '承办会议', special_issues: '承办特刊',
  academic_roles: '学术兼职', academic_reports: '学术报告',
  teaching_platforms: '教学平台建设', industry_standards: '行业标准',
}

const reviewFieldConfig = {
  papers: [
    ['authors_text', '作者'],
    ['title', '标题'],
    ['journal', '期刊'],
    ['year', '年份'],
    ['is_first_author', '是否第一作者'],
    ['is_corresponding_author', '是否通讯作者'],
    ['doi', 'DOI'],
    ['volume', '卷号'],
    ['issue', '期号'],
    ['pages', '页数'],
  ],
  projects: [
    ['project_type', '项目类型'],
    ['name', '项目名称'],
    ['project_number', '项目编号'],
    ['start_date', '开始时间'],
    ['end_date', '结束时间'],
    ['role', '身份'],
    ['amount', '金额'],
  ],
  awards: [
    ['award_name', '奖项名称'],
    ['project_name', '项目名称'],
    ['participants', '参与人员'],
    ['awarding_body', '颁奖单位'],
  ],
  patents: [
    ['applicants_text', '申请人'],
    ['patent_name', '专利名称'],
    ['application_number', '申请号'],
    ['authorization_number', '授权号'],
    ['status', '状态'],
  ],
  software_copyrights: [
    ['applicant', '申请人'],
    ['name', '软著名称'],
    ['registration_date', '登记时间'],
    ['registration_number', '登记号'],
  ],
  student_awards: [
    ['award_name', '奖项名称'],
    ['level', '等级'],
    ['role', '身份'],
    ['award_date', '获奖时间'],
  ],
  conferences: [
    ['name', '会议名称'],
    ['date', '时间'],
    ['role', '身份'],
    ['website', '网址'],
  ],
  special_issues: [
    ['issue_name', '特刊名称'],
    ['journal_name', '期刊名称'],
    ['date', '时间'],
    ['role', '身份'],
  ],
  academic_roles: [
    ['title', '头衔'],
    ['start_date', '开始时间'],
    ['end_date', '结束时间'],
  ],
  academic_reports: [
    ['name', '报告名称'],
    ['report_type', '报告类型'],
    ['date', '时间'],
  ],
  teaching_platforms: [
    ['name', '名称'],
    ['issuing_body', '发布单位'],
    ['approval_date', '获批时间'],
    ['position', '担任职位'],
  ],
  industry_standards: [
    ['name', '标准名称'],
    ['publish_date', '发布时间'],
    ['role', '身份'],
  ],
}

const fallbackFieldLabels = {
  title: '标题',
  start_date: '开始时间',
  end_date: '结束时间',
  name: '名称',
  project_type: '项目类型',
  project_number: '项目编号',
  role: '身份',
  amount: '金额',
  award_name: '奖项名称',
  project_name: '项目名称',
  participants: '参与人员',
  awarding_body: '颁奖单位',
  patent_name: '专利名称',
  application_number: '申请号',
  authorization_number: '授权号',
  status: '状态',
  applicant: '申请人',
  applicants_text: '申请人',
  authors_text: '作者',
  journal: '期刊',
  year: '年份',
  doi: 'DOI',
  is_first_author: '是否第一作者',
  is_corresponding_author: '是否通讯作者',
  issue: '期号',
  volume: '卷号',
  pages: '页数',
  registration_date: '登记时间',
  registration_number: '登记号',
  level: '等级',
  award_date: '获奖时间',
  date: '时间',
  website: '网址',
  issue_name: '特刊名称',
  journal_name: '期刊名称',
  report_type: '报告类型',
  issuing_body: '发布单位',
  approval_date: '获批时间',
  publish_date: '发布时间',
}

const metaFields = new Set(['id', 'raw_text', 'confidence', 'review_status', 'ai_review_status', 'ai_review_message'])

function confidenceType(c) {
  if (c >= 0.8) return 'success'
  if (c >= 0.5) return 'warning'
  return 'danger'
}

function aiStatusLabel(status) {
  return {
    not_reviewed: '未AI审核',
    success: 'AI成功',
    failed: 'AI失败',
  }[status] || status
}

function aiStatusType(status) {
  return {
    not_reviewed: 'info',
    success: 'success',
    failed: 'danger',
  }[status] || 'info'
}

function draftKey(entityType, id) {
  return `${entityType}:${id}`
}

function aiItemKey(entityType, id) {
  return `${entityType}:${id}`
}

function buildDraft(record) {
  const draft = {}
  Object.keys(record).forEach(key => {
    if (!metaFields.has(key)) {
      draft[key] = record[key] ?? ''
    }
  })
  return draft
}

function getDraft(entityType, record) {
  const key = draftKey(entityType, record.id)
  if (!editDrafts.value[key]) {
    editDrafts.value[key] = buildDraft(record)
  }
  return editDrafts.value[key]
}

function resetDraft(entityType, record) {
  editDrafts.value[draftKey(entityType, record.id)] = buildDraft(record)
}

function getStructuredRows(entityType, record) {
  const draft = getDraft(entityType, record)
  const configuredFields = reviewFieldConfig[entityType]
  if (configuredFields) {
    return configuredFields
      .filter(([key]) => Object.prototype.hasOwnProperty.call(draft, key))
      .map(([key, label]) => ({ key, label }))
  }
  return Object.keys(draft).map(key => ({
    key,
    label: fallbackFieldLabels[key] || key,
  }))
}

async function loadPersons() {
  const res = await api.get('/api/persons/')
  persons.value = res.data
}

async function loadAiReviewConfig() {
  try {
    const res = await api.get('/api/ai/review-config')
    aiConfigured.value = !!res.data.configured
    aiThreshold.value = Math.round((res.data.ai_review_confidence_threshold || 0.6) * 100)
    aiConcurrency.value = res.data.ai_review_concurrency || 2
    aiRetryCount.value = res.data.ai_review_retry_count || 1
    aiStatusText.value = aiConfigured.value ? '' : 'AI服务尚未配置，请先由管理员在用户管理页配置 OpenAI Responses 参数。'
  } catch (e) {
    aiConfigured.value = false
    aiStatusText.value = '无法读取AI配置。'
  }
}

async function loadPendingItems() {
  if (!selectedPerson.value) return
  try {
    const res = await api.get(`/api/reviews/pending/${selectedPerson.value}`)
    pendingItems.value = res.data
    editDrafts.value = {}
    Object.entries(res.data).forEach(([entityType, items]) => {
      items.forEach(item => {
        editDrafts.value[draftKey(entityType, item.id)] = buildDraft(item)
      })
    })
  } catch (e) {
    pendingItems.value = {}
    editDrafts.value = {}
  }
}

async function reviewItem(entityType, record, action) {
  try {
    const payload = {
      entity_type: entityType,
      entity_id: record.id,
      action,
    }
    if (action === 'approve') {
      payload.updated_fields = getDraft(entityType, record)
    }
    await api.post('/api/reviews/action', payload)
    ElMessage.success(action === 'approve' ? '已通过' : '已拒绝')
    await loadPendingItems()
  } catch (e) {}
}

async function batchApprove() {
  try {
    const res = await api.post('/api/reviews/batch-approve', {
      person_id: selectedPerson.value,
      confidence_threshold: threshold.value / 100,
    })
    ElMessage.success(res.data.msg)
    await loadPendingItems()
  } catch (e) {}
}

async function runAiReview() {
  if (!selectedPerson.value) return
  const tasks = []
  Object.entries(pendingItems.value).forEach(([entityType, items]) => {
    items.forEach(item => {
      if ((item.confidence ?? 0) <= aiThreshold.value / 100) {
        tasks.push({ entityType, item })
      }
    })
  })
  if (!tasks.length) {
    ElMessage.info('当前没有低于或等于 AI 阈值的待审核条目。')
    return
  }
  aiReviewing.value = true
  aiReviewCancelled.value = false
  let successCount = 0
  let failedCount = 0
  try {
    let cursor = 0
    let completed = 0
    const worker = async () => {
      while (cursor < tasks.length) {
        if (aiReviewCancelled.value) return
        const index = cursor
        cursor += 1
        const { entityType, item } = tasks[index]
        aiStatusText.value = `AI审核进度 ${completed + 1}/${tasks.length}：正在处理 ${entityLabels[entityType] || entityType} - ${String(item.raw_text || '').slice(0, 60)}`
        const key = aiItemKey(entityType, item.id)
        aiItemLoading.value[key] = true
        try {
          let res = null
          let attemptError = null
          for (let attempt = 0; attempt <= aiRetryCount.value; attempt += 1) {
            try {
              res = await api.post('/api/ai/review-item', {
                entity_type: entityType,
                entity_id: item.id,
              })
              attemptError = null
              break
            } catch (e) {
              attemptError = e
            }
          }
          if (res && res.data.reviewed_count > 0) {
            successCount += 1
          } else {
            failedCount += 1
            if (attemptError) item.ai_review_message = 'AI review failed after retries'
          }
          completed += 1
          await loadPendingItems()
        } catch (e) {
          failedCount += 1
          completed += 1
        } finally {
          aiItemLoading.value[key] = false
        }
      }
    }
    await Promise.all(Array.from({ length: Math.max(1, aiConcurrency.value) }, () => worker()))
    if (aiReviewCancelled.value) {
      aiStatusText.value = `AI审核已取消：已完成 ${successCount + failedCount}/${tasks.length} 条，成功 ${successCount} 条，失败 ${failedCount} 条。`
      ElMessage.warning('AI审核已取消')
      return
    }
    if (!aiReviewCancelled.value) {
      aiStatusText.value = `AI审核完成：共处理 ${tasks.length} 条，成功 ${successCount} 条，失败 ${failedCount} 条。`
      ElMessage.success(`AI审核完成：成功 ${successCount} 条，失败 ${failedCount} 条。`)
    }
  } catch (e) {
    aiStatusText.value = 'AI审核失败，请检查服务配置或网络。'
  } finally {
    aiReviewing.value = false
    aiReviewCancelled.value = false
  }
}

function cancelAiReview() {
  aiReviewCancelled.value = true
  aiStatusText.value = '正在取消 AI 审核，将在当前条目处理完成后停止。'
}

async function runSingleAiReview(entityType, record) {
  const key = aiItemKey(entityType, record.id)
  aiItemLoading.value[key] = true
  try {
    const res = await api.post('/api/ai/review-item', {
      entity_type: entityType,
      entity_id: record.id,
    })
    if (res.data.reviewed_count > 0) {
      ElMessage.success('单条 AI 审核完成，结果已回填，仍需人工通过。')
    } else {
      ElMessage.warning('单条 AI 审核未成功，请查看 AI 状态。')
    }
    await loadPendingItems()
  } catch (e) {
    ElMessage.error('单条 AI 审核失败，请检查服务配置或网络。')
  } finally {
    aiItemLoading.value[key] = false
  }
}

onMounted(async () => {
  await loadPersons()
  await loadAiReviewConfig()
})
</script>

<style scoped>
.review-expand {
  display: grid;
  gap: 16px;
}

.review-block {
  background: #f8fafc;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 14px;
}

.review-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.review-block-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.review-raw-text {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #606266;
}
</style>
