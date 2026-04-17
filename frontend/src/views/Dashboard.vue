<template>
  <div>
    <div class="page-header">
      <h2>仪表盘</h2>
    </div>
    <div class="stat-cards">
      <div class="stat-card blue">
        <div class="stat-value">{{ stats.persons || 0 }}</div>
        <div class="stat-label">人员总数</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">{{ stats.papers || 0 }}</div>
        <div class="stat-label">论文总数</div>
      </div>
      <div class="stat-card orange">
        <div class="stat-value">{{ stats.pending_reviews || 0 }}</div>
        <div class="stat-label">待审核</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-value">{{ stats.projects || 0 }}</div>
        <div class="stat-label">项目总数</div>
      </div>
    </div>
    <div class="stat-cards">
      <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
        <div class="stat-value">{{ stats.patents || 0 }}</div>
        <div class="stat-label">专利总数</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);">
        <div class="stat-value">{{ stats.awards || 0 }}</div>
        <div class="stat-label">获奖总数</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333;">
        <div class="stat-value">{{ stats.users || 0 }}</div>
        <div class="stat-label">系统用户</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({})

onMounted(async () => {
  try {
    const res = await api.get('/api/stats')
    stats.value = res.data
  } catch (e) {}
})
</script>
