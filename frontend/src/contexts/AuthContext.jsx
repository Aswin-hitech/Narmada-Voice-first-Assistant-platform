import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [officerToken, setOfficerToken] = useState(() => localStorage.getItem('narmada_officer_token'))
  const [officerUser, setOfficerUser] = useState(() => localStorage.getItem('narmada_officer_user'))
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('narmada_officer_token')
    const user = localStorage.getItem('narmada_officer_user')
    if (token) setOfficerToken(token)
    if (user) setOfficerUser(user)
  }, [])

  const login = async (username, password) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const data = await api.officerLogin(username, password)
      if (data.token) {
        localStorage.setItem('narmada_officer_token', data.token)
        localStorage.setItem('narmada_officer_user', username)
        setOfficerToken(data.token)
        setOfficerUser(username)
        return { success: true }
      } else {
        const msg = data.error || 'Login failed. Please check your credentials.'
        setAuthError(msg)
        return { success: false, error: msg }
      }
    } catch (err) {
      const msg = err.message || 'Network error. Please try again.'
      setAuthError(msg)
      return { success: false, error: msg }
    } finally {
      setAuthLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('narmada_officer_token')
    localStorage.removeItem('narmada_officer_user')
    setOfficerToken(null)
    setOfficerUser(null)
    setAuthError(null)
  }

  return (
    <AuthContext.Provider value={{ officerToken, officerUser, login, logout, authError, authLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
