<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ArrowRight, ShieldCheck } from '@lucide/vue'
import BrandMark from '../components/BrandMark.vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const displayName = ref('')
const error = ref('')
const busy = ref(false)

const redirectPath = () => {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
  return redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/home'
}

async function loadStatus() {
  const authenticated = await auth.refresh()
  if (authenticated) await router.replace(redirectPath())
}

async function submit() {
  if (busy.value) return
  error.value = ''
  busy.value = true
  try {
    if (auth.setupRequired) {
      await auth.initializeAdmin(email.value, password.value, displayName.value)
    } else {
      await auth.signIn(email.value, password.value)
    }
    await router.replace(redirectPath())
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '认证失败，请稍后重试'
  } finally {
    busy.value = false
  }
}

onMounted(() => void loadStatus())
</script>

<template>
  <main class="login-page">
    <section class="login-story" aria-label="Rovia 旅行工作台">
      <BrandMark />
      <span class="rovia-kicker">MAKE ROOM FOR THE JOURNEY</span>
      <h2>为下一程，<br />留一点期待。</h2>
      <p>从想去的地方，到每天的安排。<br />把路线、停留和沿途风景，慢慢串成自己的旅程。</p>
      <div class="rovia-route-art" aria-hidden="true"><i /><span>出发</span><b>沿途皆有可能</b><span>抵达</span></div>
    </section>
    <section class="login-panel glass-card" aria-labelledby="login-title">
      <span class="eyebrow">你的私人旅行工作台</span>
      <h1 id="login-title">{{ auth.setupRequired ? '创建管理员账户' : '登录 Rovia' }}</h1>
      <p class="login-lead">
        {{ auth.setupRequired ? '创建第一个账户，开始整理你的路线与旅行计划。' : '欢迎回来，接着安排你的下一段旅程。' }}
      </p>
      <form class="login-form" @submit.prevent="submit">
        <label><span>邮箱</span><input v-model.trim="email" type="email" autocomplete="email" placeholder="name@example.com" required></label>
        <label v-if="auth.setupRequired"><span>显示名称</span><input v-model.trim="displayName" autocomplete="name" placeholder="管理员" required></label>
        <label><span>密码</span><input v-model="password" type="password" :autocomplete="auth.setupRequired ? 'new-password' : 'current-password'" placeholder="至少 8 位字符" minlength="8" required></label>
        <p v-if="error" class="login-error" role="alert">{{ error }}</p>
        <button class="login-submit" type="submit" :disabled="busy">
          <ShieldCheck v-if="auth.setupRequired" :size="18" />
          <ArrowRight v-else :size="18" />
          {{ busy ? '处理中…' : auth.setupRequired ? '创建并进入工作台' : '进入工作台' }}
        </button>
      </form>
      <small class="login-note">账户数据按用户隔离；管理员可以创建普通用户。</small>
    </section>
  </main>
</template>
