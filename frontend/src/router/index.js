import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/showcase/:id?',
    name: 'ShowcasePage',
    component: () => import('../views/ShowcasePage.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'persons', name: 'PersonList', component: () => import('../views/PersonList.vue') },
      { path: 'persons/:id', name: 'PersonDetail', component: () => import('../views/PersonDetail.vue'), props: true },
      { path: 'attachments', name: 'AttachmentManager', component: () => import('../views/AttachmentManager.vue') },
      { path: 'upload/:personId', name: 'ResumeUpload', component: () => import('../views/ResumeUpload.vue'), props: true },
      { path: 'reviews', name: 'ReviewPage', component: () => import('../views/ReviewPage.vue') },
      { path: 'users', name: 'UserManagement', component: () => import('../views/UserManagement.vue') },
      { path: 'export', name: 'ExportPage', component: () => import('../views/ExportPage.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
