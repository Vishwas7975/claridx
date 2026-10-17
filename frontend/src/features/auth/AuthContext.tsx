import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, onUnauthorized, setAuthToken } from '../../api/client'
import { toApiError } from '../../api/errors'
import type { LoginRequest, UserProfile } from '../../api/types'

const TOKEN_STORAGE_KEY = 'claridx_token'
const USER_STORAGE_KEY = 'claridx_user'

export interface AuthContextValue {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
}

const defaultContext: AuthContextValue = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  login: async () => {},
  logout: () => {},
}

const AuthContext = createContext<AuthContextValue>(defaultContext)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(TOKEN_STORAGE_KEY)
    } catch {
      return null
    }
  })

  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const raw = sessionStorage.getItem(USER_STORAGE_KEY)
      return raw ? (JSON.parse(raw) as UserProfile) : null
    } catch {
      return null
    }
  })

  const [isLoading, setIsLoading] = useState<boolean>(() => {
    try {
      const storedToken = sessionStorage.getItem(TOKEN_STORAGE_KEY)
      const storedUser = sessionStorage.getItem(USER_STORAGE_KEY)
      if (!storedToken) return false
      if (storedUser) return false
      return true
    } catch {
      return false
    }
  })

  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY)
      sessionStorage.removeItem(USER_STORAGE_KEY)
    } catch {
      // Ignore storage errors on teardown
    }
    setAuthToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  const login = useCallback(async ({ email, password }: LoginRequest) => {
    const { data, error, response } = await api.POST('/api/v1/auth/login', {
      body: { email: email.trim(), password },
    })
    if (data === undefined) {
      throw toApiError(error, response.status)
    }

    const receivedToken = data.access_token
    setAuthToken(receivedToken)

    const { data: meData, error: meError, response: meResponse } = await api.GET('/api/v1/auth/me')
    if (meData === undefined) {
      setAuthToken(null)
      throw toApiError(meError, meResponse.status)
    }

    try {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, receivedToken)
      sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(meData))
    } catch {
      // Storage might be restricted; session will remain in memory
    }
    setTokenState(receivedToken)
    setUser(meData)
  }, [])

  useEffect(() => {
    onUnauthorized(() => {
      logout()
    })
    return () => {
      onUnauthorized(null)
    }
  }, [logout])

  useEffect(() => {
    let active = true
    async function initSession() {
      const storedToken = (() => {
        try {
          return sessionStorage.getItem(TOKEN_STORAGE_KEY)
        } catch {
          return null
        }
      })()

      if (!storedToken) {
        if (active) {
          setIsLoading(false)
        }
        return
      }

      setAuthToken(storedToken)
      try {
        const { data: meData } = await api.GET('/api/v1/auth/me')
        if (!active) return
        if (meData !== undefined) {
          setUser(meData)
          setTokenState(storedToken)
          try {
            sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(meData))
          } catch {
            // Ignore
          }
        } else {
          logout()
        }
      } catch {
        if (active) {
          logout()
        }
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    void initSession()

    return () => {
      active = false
    }
  }, [logout])

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: Boolean(user && token),
    isLoading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}
