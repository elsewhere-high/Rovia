import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import TripPlanView from '../views/TripPlanView.vue'
import OpsView from '../views/OpsView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import { useAuthStore } from '../stores/auth'
import { pinia } from '../stores/pinia'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: (_to, _from, savedPosition) => savedPosition || { top: 0 },
  routes: [
    { path: '/login', component: LoginView, meta: { title: '登录' } },
    { path: '/', redirect: '/home' },
    { path: '/home', component: HomeView, meta: { requiresAuth: true, title: '旅行工作台' } },
    { path: '/trips/:tripId/plan', component: TripPlanView, meta: { requiresAuth: true, title: '行程安排' } },
    { path: '/ops', component: OpsView, meta: { requiresAuth: true, title: '运行监控' } },
    { path: '/:pathMatch(.*)*', component: NotFoundView, meta: { title: '页面未找到' } },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const auth = useAuthStore(pinia)
  if (await auth.ensureAuthenticated()) return true
  return { path: '/login', query: { redirect: to.fullPath } }
})

router.afterEach((to) => {
  document.title = `${to.meta.title || '旅行工作台'} · Rovia`
})

export default router
