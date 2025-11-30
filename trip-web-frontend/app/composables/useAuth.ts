import type { User, LoginRequest, RegisterRequest, AuthResponse } from '~/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

export const useAuth = () => {
  const state = useState<AuthState>('auth', () => ({
    user: null,
    token: null,
    isAuthenticated: false,
  }))

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Initialize auth state from localStorage on client side
  const initAuth = () => {
    if (import.meta.client) {
      const storedToken = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('auth_user')
      
      if (storedToken && storedUser) {
        try {
          state.value = {
            token: storedToken,
            user: JSON.parse(storedUser),
            isAuthenticated: true,
          }
        } catch {
          // Invalid stored data, clear it
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
        }
      }
    }
  }

  /**
   * Login user
   */
  const login = async (credentials: LoginRequest): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      // TODO: Replace with actual API call when user service is ready
      // Simulated login for now
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock response
      const mockUser: User = {
        id: 'user-' + Math.random().toString(36).slice(2, 11),
        username: credentials.username,
        email: `${credentials.username}@example.com`,
        createdAt: new Date().toISOString(),
      }
      
      const mockToken = 'mock-jwt-token-' + Math.random().toString(36).slice(2, 11)
      
      // Store auth data
      state.value = {
        user: mockUser,
        token: mockToken,
        isAuthenticated: true,
      }

      if (import.meta.client) {
        localStorage.setItem('auth_token', mockToken)
        localStorage.setItem('auth_user', JSON.stringify(mockUser))
      }

      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register new user
   */
  const register = async (data: RegisterRequest): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      // TODO: Replace with actual API call when user service is ready
      // Simulated registration for now
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Mock response
      const mockUser: User = {
        id: 'user-' + Math.random().toString(36).slice(2, 11),
        username: data.username,
        email: data.email,
        createdAt: new Date().toISOString(),
      }
      
      const mockToken = 'mock-jwt-token-' + Math.random().toString(36).slice(2, 11)
      
      // Store auth data
      state.value = {
        user: mockUser,
        token: mockToken,
        isAuthenticated: true,
      }

      if (import.meta.client) {
        localStorage.setItem('auth_token', mockToken)
        localStorage.setItem('auth_user', JSON.stringify(mockUser))
      }

      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Registration failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout user
   */
  const logout = () => {
    state.value = {
      user: null,
      token: null,
      isAuthenticated: false,
    }

    if (import.meta.client) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    }
  }

  /**
   * Get current user
   */
  const currentUser = computed(() => state.value.user)

  /**
   * Get auth token
   */
  const token = computed(() => state.value.token)

  /**
   * Check if user is authenticated
   */
  const isAuthenticated = computed(() => state.value.isAuthenticated)

  /**
   * Get user ID (with fallback for demo purposes)
   */
  const userId = computed(() => state.value.user?.id || 'demo-user')

  return {
    isLoading: readonly(isLoading),
    error: readonly(error),
    currentUser,
    token,
    isAuthenticated,
    userId,
    initAuth,
    login,
    register,
    logout,
  }
}
