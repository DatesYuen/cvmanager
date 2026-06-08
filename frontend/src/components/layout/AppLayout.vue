<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="24"><Document /></el-icon>
        <span>CV Manager</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1d1e3a"
        text-color="#a0a3bd"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-sub-menu index="/person-management">
          <template #title>
            <el-icon><User /></el-icon>
            <span>人员管理</span>
          </template>
          <el-menu-item index="/persons">
            <el-icon><User /></el-icon>
            <span>人员列表</span>
          </el-menu-item>
          <el-menu-item index="/attachments">
            <el-icon><FolderOpened /></el-icon>
            <span>附件管理</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/reviews">
          <el-icon><Checked /></el-icon>
          <span>审核管理</span>
        </el-menu-item>
        <el-menu-item index="/export">
          <el-icon><Download /></el-icon>
          <span>数据导出</span>
        </el-menu-item>
        <el-menu-item index="/users" v-if="auth.isAdmin">
          <el-icon><Setting /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top-header">
        <div></div>
        <div class="header-right">
          <span class="user-name">{{ auth.user?.display_name || auth.user?.username }}</span>
          <el-tag size="small" :type="auth.isAdmin ? 'danger' : 'info'">
            {{ auth.isAdmin ? '管理员' : '用户' }}
          </el-tag>
          <el-button text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => route.path)

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.sidebar {
  background: #1d1e3a;
  overflow-y: auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: white;
  font-size: 18px;
  font-weight: 700;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.el-menu {
  border-right: none;
}

.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 0 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-weight: 500;
  color: var(--text-primary);
}

.main-content {
  padding: 24px;
  background: var(--bg-color);
  overflow-y: auto;
}

@media (max-width: 900px) {
  .app-layout {
    display: block;
    height: auto;
    min-height: 100vh;
  }

  .sidebar {
    width: 100% !important;
  }

  .top-header {
    padding: 12px 16px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .main-content {
    padding: 16px;
  }
}
</style>
