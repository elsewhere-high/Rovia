import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  getAuthStatus,
  login,
  logout,
  setupAdmin,
  type User,
} from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const setupRequired = ref(false)
  const initialized = ref(false)
  const loading = ref(false)

  const isAdmin = computed(() => user.value?.role === 'admin')

  async function refresh() {
    loading.value = true
    try {
      const status = await getAuthStatus()
      user.value = status.user
      setupRequired.value = status.setup_required
      initialized.value = true
      return Boolean(user.value)
    } catch {
      user.value = null
      initialized.value = true
      return false
    } finally {
      loading.value = false
    }
  }

  async function ensureAuthenticated() {
    if (initialized.value) return Boolean(user.value)
    return refresh()
  }

  function setUser(value: User) {
    user.value = value
    setupRequired.value = false
    initialized.value = true
  }

  async function signIn(email: string, password: string) {
    setUser(await login(email, password))
  }

  async function initializeAdmin(email: string, password: string, displayName: string) {
    setUser(await setupAdmin({ email, password, display_name: displayName }))
  }

  async function signOut() {
    await logout().catch(() => undefined)
    user.value = null
    initialized.value = true
  }

  return {
    user,
    setupRequired,
    initialized,
    loading,
    isAdmin,
    refresh,
    ensureAuthenticated,
    setUser,
    signIn,
    initializeAdmin,
    signOut,
  }
})
