import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, clearToken, getToken, setToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // loading | authed | guest

  const loadUser = useCallback(async () => {
    if (!getToken()) {
      setStatus('guest')
      return
    }
    try {
      const me = await api.me()
      setUser(me)
      setStatus('authed')
    } catch {
      clearToken()
      setStatus('guest')
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = async (email, password) => {
    const { access_token } = await api.login(email, password)
    setToken(access_token)
    await loadUser()
  }

  const register = async (name, email, password) => {
    await api.register(name, email, password)
    await login(email, password)
  }

  const logout = () => {
    clearToken()
    setUser(null)
    setStatus('guest')
  }

  const refreshUser = async () => {
    const me = await api.me()
    setUser(me)
    return me
  }

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
