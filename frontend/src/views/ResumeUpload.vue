<template>
  <div>
    <div class="page-header">
      <div style="display:flex; align-items:center; gap:12px">
        <el-button @click="$router.back()" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h2>上传简历</h2>
      </div>
    </div>
    <div class="card-container">
      <el-upload
        ref="uploadRef"
        drag
        :action="`/api/resumes/upload/${personId}`"
        :headers="{ Authorization: `Bearer ${auth.token}` }"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :before-upload="beforeUpload"
        :limit="1"
        accept=".docx"
        :auto-upload="true"
      >
        <el-icon size="60" style="color:#409eff"><UploadFilled /></el-icon>
        <div style="margin-top:12px; font-size:16px; color:#606266">
          将DOCX文件拖到此处，或 <em style="color:#409eff">点击上传</em>
        </div>
        <div style="margin-top:8px; color:#909399; font-size:13px">
          仅支持 .docx 格式的简历文件
        </div>
      </el-upload>

      <div v-if="uploading" style="margin-top:24px; text-align:center">
        <el-progress :percentage="100" status="success" :indeterminate="true" />
        <p style="color:#909399; margin-top:8px">正在解析简历，请稍候...</p>
      </div>

      <div v-if="parseResult" style="margin-top:24px">
        <el-alert type="success" :closable="false" show-icon>
          简历上传并解析完成！已自动提取数据并与现有数据进行差异对比。
        </el-alert>
        <el-button type="primary" style="margin-top:16px" @click="$router.push(`/persons/${personId}`)">
          查看解析结果
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const props = defineProps({ personId: [String, Number] })
const auth = useAuthStore()
const uploading = ref(false)
const parseResult = ref(null)

function beforeUpload(file) {
  if (!file.name.endsWith('.docx')) {
    ElMessage.error('仅支持 .docx 格式文件')
    return false
  }
  uploading.value = true
  return true
}

function onUploadSuccess(res) {
  uploading.value = false
  parseResult.value = res
  ElMessage.success('简历上传并解析成功')
}

function onUploadError() {
  uploading.value = false
  ElMessage.error('上传失败')
}
</script>
