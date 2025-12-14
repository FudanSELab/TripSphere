'use client'

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User, LoginRequest, RegisterRequest } from '@/lib/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  _hasHydrated: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
  setHasHydrated: (hasHydrated: boolean) => void
  login: (credentials: LoginRequest) => Promise<boolean>
  register: (data: RegisterRequest) => Promise<boolean>
  logout: () => void
  initAuth: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      _hasHydrated: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      setError: (error) => set({ error }),
      setLoading: (isLoading) => set({ isLoading }),
      setHasHydrated: (hasHydrated) => set({ _hasHydrated: hasHydrated }),

      initAuth: () => {
        const state = get()
        if (state.token && state.user) {
          set({ isAuthenticated: true })
        }
      },

      login: async (credentials: LoginRequest): Promise<boolean> => {
        set({ isLoading: true, error: null })

        try {
          // Validate input
          if (!credentials.username || !credentials.password) {
            set({ error: 'Username and password are required', isLoading: false })
            return false
          }

          // Sanitize username for mock email
          const sanitizedUsername = credentials.username.replace(/[^a-zA-Z0-9_-]/g, '')
          
          // TODO: Replace with actual API call when user service is ready
          // Simulated login for now
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          // Mock response
          const mockUser: User = {
            id: 'user-' + Math.random().toString(36).slice(2, 11),
            username: sanitizedUsername,
            email: `${sanitizedUsername}@example.com`,
            createdAt: new Date().toISOString(),
          }
          
          const mockToken = 'mock-jwt-token-' + Math.random().toString(36).slice(2, 11)
          
          // Store auth data
          set({
            user: mockUser,
            token: mockToken,
            isAuthenticated: true,
            isLoading: false,
          })

          return true
        } catch (e) {
          const errorMessage = e instanceof Error ? e.message : 'Login failed'
          set({ error: errorMessage, isLoading: false })
          return false
        }
      },

      register: async (data: RegisterRequest): Promise<boolean> => {
        set({ isLoading: true, error: null })

        try {
          // Validate input
          if (!data.username || !data.email || !data.password) {
            set({ error: 'All fields are required', isLoading: false })
            return false
          }

          // Sanitize username
          const sanitizedUsername = data.username.replace(/[^a-zA-Z0-9_-]/g, '')
          
          // Basic email validation
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          if (!emailRegex.test(data.email)) {
            set({ error: 'Invalid email address', isLoading: false })
            return false
          }

          // TODO: Replace with actual API call when user service is ready
          // Simulated registration for now
          await new Promise(resolve => setTimeout(resolve, 1000))

          // Mock response
          const mockUser: User = {
            id: 'user-' + Math.random().toString(36).slice(2, 11),
            username: sanitizedUsername,
            email: data.email,
            createdAt: new Date().toISOString(),
          }
          
          const mockToken = 'mock-jwt-token-' + Math.random().toString(36).slice(2, 11)
          
          // Store auth data
          set({
            user: mockUser,
            token: mockToken,
            isAuthenticated: true,
            isLoading: false,
          })

          return true
        } catch (e) {
          const errorMessage = e instanceof Error ? e.message : 'Registration failed'
          set({ error: errorMessage, isLoading: false })
          return false
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)

// Helper hooks
export const useUserId = () => {
  const user = useAuth((state) => state.user)
  return user?.id || 'demo-user'
}

export const useIsAuthenticated = () => {
  return useAuth((state) => state.isAuthenticated)
}
