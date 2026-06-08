<template>
  <div>
    <div class="page-header">
      <h2>附件管理</h2>
      <el-select v-model="selectedPersonId" placeholder="选择人员" filterable style="width:240px" @change="loadAttachments">
        <el-option v-for="person in persons" :key="person.id" :label="person.name" :value="person.id" />
      </el-select>
    </div>

    <div class="card-container">
      <div class="upload-grid">
        <el-upload
          drag
          :http-request="startSmartUpload"
          :show-file-list="false"
          :disabled="!selectedPersonId"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-title">智能归档上传</div>
          <div class="upload-subtitle">拖拽文件到此处，或点击选择</div>
        </el-upload>

        <el-upload
          drag
          :http-request="uploadToFolder"
          :show-file-list="false"
          :disabled="!uploadFolderId"
        >
          <el-icon class="upload-icon"><FolderOpened /></el-icon>
          <div class="upload-title">上传到文件夹</div>
          <div class="upload-subtitle">{{ uploadFolderId ? '拖拽文件到此处，或点击选择' : '请先选择上传文件夹' }}</div>
        </el-upload>
      </div>

      <div class="toolbar">
        <el-input v-model="folderName" placeholder="新文件夹名称" style="width:220px" />
        <el-select v-model="parentFolderId" placeholder="上级文件夹" clearable style="width:240px">
          <el-option v-for="folder in folders" :key="folder.id" :label="folder.hierarchy" :value="folder.id" />
        </el-select>
        <el-button @click="createFolder" :disabled="!selectedPersonId">
          <el-icon><FolderAdd /></el-icon> 新增文件夹
        </el-button>
        <el-select v-model="uploadFolderId" placeholder="选择上传文件夹" clearable style="width:240px">
          <el-option v-for="folder in folders" :key="folder.id" :label="folder.hierarchy" :value="folder.id" />
        </el-select>
      </div>

      <div class="toolbar export-row">
        <el-button type="success" @click="exportChecked" :disabled="!checkedAttachmentIds.length">
          <el-icon><Download /></el-icon> 导出选中
        </el-button>
        <el-button type="success" plain @click="exportAll" :disabled="!selectedPersonId">
          <el-icon><Download /></el-icon> 导出全部
        </el-button>
        <span class="hint">已选择 {{ checkedAttachmentIds.length }} 个附件</span>
      </div>

      <el-tree
        ref="treeRef"
        class="attachment-tree"
        :data="treeData"
        node-key="key"
        show-checkbox
        default-expand-all
        :expand-on-click-node="false"
        @check="handleTreeCheck"
      >
        <template #default="{ data }">
          <div class="tree-node">
            <div class="tree-node-main">
              <el-icon v-if="data.type === 'folder'"><Folder /></el-icon>
              <el-icon v-else><Document /></el-icon>
              <span>{{ data.label }}</span>
              <el-tag v-if="data.attachment?.is_placeholder" size="small" type="info">暂无</el-tag>
              <span v-if="data.attachment" class="node-meta">{{ formatDate(data.attachment.uploaded_at) }}</span>
            </div>
            <div v-if="data.attachment" class="node-actions">
              <el-button size="small" @click.stop="previewAttachment(data.attachment.id)">查看</el-button>
              <el-button size="small" @click.stop="downloadAttachment(data.attachment.id)">下载</el-button>
              <el-button size="small" type="danger" @click.stop="deleteAttachment(data.attachment.id)">删除</el-button>
            </div>
            <div v-else-if="data.type === 'folder' && data.folder?.id" class="node-actions">
              <el-button size="small" type="danger" @click.stop="deleteFolder(data.folder)">删除</el-button>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <el-dialog v-model="showMatchDialog" title="选择附件归属" width="780px">
      <div class="match-header">
        <span class="match-filename" :title="pendingFile?.name">文件：{{ pendingFile?.name }}</span>
        <el-radio v-model="selectedTarget" label="only">仅上传，不关联条目</el-radio>
      </div>
      <el-table :data="matchCandidates" stripe size="small" max-height="360">
        <el-table-column label="选择" width="70">
          <template #default="{ row }">
            <el-radio v-model="selectedTarget" :label="targetKey(row)">&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类型" width="120" />
        <el-table-column prop="item_name" label="可能匹配条目" min-width="360" show-overflow-tooltip />
        <el-table-column label="匹配度" width="100">
          <template #default="{ row }">{{ Math.round(row.score * 100) }}%</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="cancelSmartUpload">取消</el-button>
        <el-button type="primary" @click="confirmSmartUpload" :loading="uploading">确认上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const persons = ref([])
const selectedPersonId = ref(null)
const folders = ref([])
const attachments = ref([])
const checkedAttachmentIds = ref([])
const folderName = ref('')
const parentFolderId = ref(null)
const uploadFolderId = ref(null)
const treeRef = ref(null)
const showMatchDialog = ref(false)
const pendingFile = ref(null)
const pendingUploadOptions = ref(null)
const matchCandidates = ref([])
const selectedTarget = ref('only')
const uploading = ref(false)

const treeData = computed(() => buildTree(folders.value, attachments.value))

async function loadPersons() {
  const res = await api.get('/api/persons/', { params: { page_size: 5000 } })
  persons.value = res.data
  if (!selectedPersonId.value && persons.value.length) {
    selectedPersonId.value = persons.value[0].id
    await loadAttachments()
  }
}

async function loadAttachments() {
  if (!selectedPersonId.value) return
  const res = await api.get(`/api/attachments/person/${selectedPersonId.value}`)
  folders.value = res.data.folders || []
  attachments.value = res.data.attachments || []
  checkedAttachmentIds.value = []
  const validFolderIds = new Set(folders.value.map(folder => folder.id))
  if (parentFolderId.value && !validFolderIds.has(parentFolderId.value)) {
    parentFolderId.value = null
  }
  if (uploadFolderId.value && !validFolderIds.has(uploadFolderId.value)) {
    uploadFolderId.value = null
  }
}

async function createFolder() {
  if (!folderName.value.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  await api.post('/api/attachments/folders', {
    person_id: selectedPersonId.value,
    name: folderName.value.trim(),
    parent_id: parentFolderId.value,
  })
  folderName.value = ''
  parentFolderId.value = null
  ElMessage.success('文件夹已创建')
  await loadAttachments()
}

async function startSmartUpload(options) {
  pendingFile.value = options.file
  pendingUploadOptions.value = options
  selectedTarget.value = 'only'
  const res = await api.get('/api/attachments/match', {
    params: { person_id: selectedPersonId.value, filename: options.file.name }
  })
  matchCandidates.value = res.data || []
  if (matchCandidates.value.length) {
    selectedTarget.value = targetKey(matchCandidates.value[0])
  }
  showMatchDialog.value = true
}

function cancelSmartUpload() {
  pendingUploadOptions.value?.onError?.(new Error('cancelled'))
  pendingFile.value = null
  pendingUploadOptions.value = null
  showMatchDialog.value = false
}

async function confirmSmartUpload() {
  if (!pendingFile.value) return
  uploading.value = true
  const form = new FormData()
  form.append('person_id', selectedPersonId.value)
  form.append('file', pendingFile.value)
  if (selectedTarget.value !== 'only') {
    const [entityType, entityId] = selectedTarget.value.split(':')
    form.append('target_entity_type', entityType)
    form.append('target_entity_id', entityId)
  }
  try {
    const res = await api.post('/api/attachments/person-upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    pendingUploadOptions.value?.onSuccess?.(res.data)
    ElMessage.success('上传成功')
    showMatchDialog.value = false
    pendingFile.value = null
    pendingUploadOptions.value = null
    await loadAttachments()
  } catch (e) {
    pendingUploadOptions.value?.onError?.(e)
  } finally {
    uploading.value = false
  }
}

async function uploadToFolder(options) {
  const form = new FormData()
  form.append('file', options.file)
  try {
    const res = await api.post(`/api/attachments/folders/${uploadFolderId.value}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    options.onSuccess?.(res.data)
    ElMessage.success('上传成功')
    await loadAttachments()
  } catch (e) {
    options.onError?.(e)
  }
}

async function previewAttachment(id) {
  const res = await api.get(`/api/attachments/preview/${id}`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60000)
}

async function downloadAttachment(id) {
  const res = await api.get(`/api/attachments/download/${id}`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = getFilenameFromHeaders(res.headers['content-disposition']) || 'attachment'
  a.click()
  URL.revokeObjectURL(url)
}

async function deleteAttachment(id) {
  try {
    await ElMessageBox.confirm('确定删除此附件吗？', '确认删除', { type: 'warning' })
    await api.delete(`/api/attachments/${id}`)
    ElMessage.success('删除成功')
    await loadAttachments()
  } catch (e) {}
}

async function deleteFolder(folder) {
  try {
    await ElMessageBox.confirm(
      `确定删除文件夹“${folder.name}”及其下所有子文件夹和附件吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await api.delete(`/api/attachments/folders/${folder.id}`)
    ElMessage.success('文件夹已删除')
    await loadAttachments()
  } catch (e) {}
}

function handleTreeCheck() {
  const checked = treeRef.value?.getCheckedNodes(false, true) || []
  checkedAttachmentIds.value = checked
    .filter(node => node.type === 'file' && node.attachment?.id)
    .map(node => node.attachment.id)
}

async function exportChecked() {
  await exportAttachments(checkedAttachmentIds.value)
}

async function exportAll() {
  await exportAttachments([])
}

async function exportAttachments(ids) {
  const res = await api.post('/api/attachments/export', {
    person_id: selectedPersonId.value,
    attachment_ids: ids,
  }, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = getFilenameFromHeaders(res.headers['content-disposition']) || 'attachments.zip'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('附件导出成功')
}

function buildTree(folderRows, attachmentRows) {
  const roots = []
  const folderNodes = new Map()

  folderRows.forEach(folder => {
    folderNodes.set(folder.id, {
      key: `folder:${folder.id}`,
      type: 'folder',
      label: folder.name,
      folder,
      children: [],
    })
  })

  folderRows.forEach(folder => {
    const node = folderNodes.get(folder.id)
    const parent = folder.parent_id ? folderNodes.get(folder.parent_id) : null
    if (parent) parent.children.push(node)
    else roots.push(node)
  })

  attachmentRows.forEach(attachment => {
    const fileNode = {
      key: `attachment:${attachment.id}`,
      type: 'file',
      label: attachment.original_filename,
      attachment,
      children: [],
    }
    if (attachment.folder_id && folderNodes.has(attachment.folder_id)) {
      folderNodes.get(attachment.folder_id).children.push(fileNode)
      return
    }
    const parts = (attachment.hierarchy || attachment.category || '未分类').split('/').filter(Boolean)
    let current = ensureRoot(roots, parts.shift() || '未分类')
    parts.forEach(part => {
      current = ensureChild(current, part)
    })
    current.children.push(fileNode)
  })

  return roots
}

function ensureRoot(roots, label) {
  let node = roots.find(item => item.label === label)
  if (!node) {
    node = { key: `root:${label}`, type: 'folder', label, children: [] }
    roots.push(node)
  }
  return node
}

function ensureChild(parent, label) {
  let node = parent.children.find(item => item.type === 'folder' && item.label === label)
  if (!node) {
    node = { key: `${parent.key}/${label}`, type: 'folder', label, children: [] }
    parent.children.push(node)
  }
  return node
}

function targetKey(row) {
  return `${row.entity_type}:${row.entity_id}`
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
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

onMounted(loadPersons)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.upload-grid :deep(.el-upload) {
  width: 100%;
}

.upload-grid :deep(.el-upload-dragger) {
  width: 100%;
  padding: 18px;
}

.upload-icon {
  font-size: 34px;
  color: #409eff;
}

.upload-title {
  margin-top: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.upload-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}

.export-row {
  justify-content: flex-start;
}

.hint,
.node-meta {
  color: #909399;
  font-size: 13px;
}

.attachment-tree {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px 0;
}

.attachment-tree :deep(.el-tree-node__content) {
  height: auto;
  min-height: 38px;
  align-items: flex-start;
  padding-top: 6px;
  padding-bottom: 6px;
}

.attachment-tree :deep(.el-tree-node__expand-icon) {
  margin-top: 4px;
}

.tree-node {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-right: 12px;
  line-height: 1.5;
}

.tree-node-main {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 2px;
}

.tree-node-main span:first-of-type {
  white-space: normal;
  overflow-wrap: anywhere;
}

.node-actions {
  flex: none;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.match-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.match-filename {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.match-header :deep(.el-radio) {
  flex: none;
  margin-right: 0;
}

@media (max-width: 900px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }
}
</style>
