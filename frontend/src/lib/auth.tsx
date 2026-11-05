import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError, api, getToken, setToken } from './api'

interface AuthState {
  ready: boolean
  role: string | null
  userId: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const [role, setRole] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    if (!getToken()) {
      setReady(true)
      return
    }
    api
      .me()
      .then((me) => {
        setRole(me.role)
        setUserId(me.user_id)
      })
      .catch(() => setToken(null))
      .finally(() => setReady(true))
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      ready,
      role,
      userId,
      async login(username: string, password: string) {
        const result = await api.login(username, password)
        setToken(result.access_token)
        const me = await api.me()
        setRole(me.role)
        setUserId(me.user_id)
      },
      logout() {
        setToken(null)
        setRole(null)
        setUserId(null)
      },
    }),
    [ready, role, userId],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth вне AuthProvider')
  return context
}

export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403)
}
