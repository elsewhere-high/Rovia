const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export interface User {
  id: string
  email: string
  display_name: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

export interface AuthStatus {
  setup_required: boolean
  authenticated: boolean
  user: User | null
}

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.error?.message || `认证请求失败（${response.status}）`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const withCredentials: RequestInit = { credentials: 'include' }

export async function getAuthStatus(): Promise<AuthStatus> {
  return json(await fetch(`${API_BASE}/api/v1/auth/status`, withCredentials))
}

export async function setupAdmin(payload: {
  email: string
  password: string
  display_name: string
}): Promise<User> {
  return json(await fetch(`${API_BASE}/api/v1/auth/setup`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }))
}

export async function login(email: string, password: string): Promise<User> {
  return json(await fetch(`${API_BASE}/api/v1/auth/login`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }))
}

export async function getMe(): Promise<User> {
  return json(await fetch(`${API_BASE}/api/v1/auth/me`, withCredentials))
}

export async function logout(): Promise<void> {
  await json(await fetch(`${API_BASE}/api/v1/auth/logout`, {
    ...withCredentials,
    method: 'POST',
  }))
}

export async function listManagedUsers(): Promise<User[]> {
  return json(await fetch(`${API_BASE}/api/v1/auth/users`, withCredentials))
}

export async function createManagedUser(payload: {
  email: string
  password: string
  display_name: string
}): Promise<User> {
  return json(await fetch(`${API_BASE}/api/v1/auth/users`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }))
}
