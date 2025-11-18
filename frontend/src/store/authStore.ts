import { create } from 'zustand'
import { authApi } from '@/lib/api'

interface User {
  id: string
  email: string
  full_name: string
  tenant_id: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setToken: (token: string) => void
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const response = await authApi.login(email, password)
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      set({ token: access_token, isAuthenticated: true })

      // Fetch user data
      const userResponse = await authApi.getCurrentUser()
      set({ user: userResponse.data, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  setToken: (token: string) => {
    localStorage.setItem('token', token)
    set({ token, isAuthenticated: true })
  },

  fetchUser: async () => {
    set({ isLoading: true })
    try {
      const response = await authApi.getCurrentUser()
      set({ user: response.data, isLoading: false })
    } catch (error) {
      set({ isLoading: false, user: null, token: null, isAuthenticated: false })
      localStorage.removeItem('token')
      throw error
    }
  },
}))
