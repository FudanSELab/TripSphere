"use client";

import {
  getCurrentUser as getCurrentUserApi,
  login as loginApi,
  logout as logoutApi,
  signup as registerApi,
} from "@/lib/requests/user/user";
import type { LoginRequest, RegisterRequest, User } from "@/lib/types";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  login: (credentials: LoginRequest) => Promise<boolean>;
  register: (data: RegisterRequest) => Promise<boolean>;
  logout: () => Promise<void>;
  initAuth: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setError: (error) => set({ error }),
      setLoading: (isLoading) => set({ isLoading }),

      // Initialize auth state by checking cookie-based session
      initAuth: async () => {
        const state = get();

        // Skip if already authenticated or currently loading
        if (state.isAuthenticated || state.isLoading) {
          return;
        }

        set({ isLoading: true });

        try {
          // Try to get current user from BFF (which will check cookie)
          const response = await getCurrentUserApi();

          if (response.code === "Success" && response.data) {
            set({
              user: response.data,
              isAuthenticated: true,
              isLoading: false,
            });
          } else {
            // No valid session
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
            });
          }
        } catch (e) {
          // Failed to check auth, clear state
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      // Check authentication status from server
      checkAuth: async (): Promise<boolean> => {
        try {
          const response = await getCurrentUserApi();

          if (response.code === "Success" && response.data) {
            set({
              user: response.data,
              isAuthenticated: true,
            });
            return true;
          } else {
            set({
              user: null,
              isAuthenticated: false,
            });
            return false;
          }
        } catch (e) {
          set({
            user: null,
            isAuthenticated: false,
          });
          return false;
        }
      },

      login: async (credentials: LoginRequest): Promise<boolean> => {
        set({ isLoading: true, error: null });

        try {
          // Validate input
          if (!credentials.username || !credentials.password) {
            set({
              error: "Username and password are required",
              isLoading: false,
            });
            return false;
          }

          // Call login API - BFF will set cookie with token
          const response = await loginApi(credentials);

          if (response.code !== "Success") {
            set({ error: response.msg, isLoading: false });
            return false;
          }

          // Store user data only (token is in httpOnly cookie managed by BFF)
          console.log("user:", response.data.user);
          set({
            user: response.data.user,
            isAuthenticated: true,
            isLoading: false,
          });

          return true;
        } catch (e) {
          const errorMessage = e instanceof Error ? e.message : "Login failed";
          set({ error: errorMessage, isLoading: false });
          return false;
        }
      },

      register: async (data: RegisterRequest): Promise<boolean> => {
        set({ isLoading: true, error: null });

        try {
          // Validate input
          if (!data.username || !data.password) {
            set({
              error: "Username and password are required",
              isLoading: false,
            });
            return false;
          }

          // Call registration API
          const response = await registerApi(data);

          if (response.code !== "Success") {
            set({ error: response.msg, isLoading: false });
            return false;
          }

          set({ isLoading: false, error: null });

          return true;
        } catch (e) {
          const errorMessage =
            e instanceof Error ? e.message : "Registration failed";
          set({ error: errorMessage, isLoading: false });
          return false;
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null });

        try {
          // Call logout API - BFF will clear cookie
          await logoutApi();

          // Clear local user data
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        } catch (e) {
          // Even if API call fails, clear local state
          const errorMessage = e instanceof Error ? e.message : "Logout failed";
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage,
          });
        }
      },
    }),
    {
      name: "auth-storage", // localStorage key
      partialize: (state) => ({
        // Only persist user info, not token (token is in httpOnly cookie)
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
