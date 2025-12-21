"use client";

import {
  login as loginApi,
  logout as logoutApi,
  register as registerApi,
} from "@/lib/requests/user/user";
import type { LoginRequest, RegisterRequest, User } from "@/lib/types";
import { create } from "zustand";

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
  initAuth: () => void;
}

export const useAuth = create<AuthState>()((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setError: (error) => set({ error }),
  setLoading: (isLoading) => set({ isLoading }),

  initAuth: () => {
    const state = get();
    if (state.user) {
      set({ isAuthenticated: true });
    }
  },

  login: async (credentials: LoginRequest): Promise<boolean> => {
    set({ isLoading: true, error: null });

    try {
      // Validate input
      if (!credentials.username || !credentials.password) {
        set({ error: "Username and password are required", isLoading: false });
        return false;
      }

      // Call login API
      const response = await loginApi(credentials);

      if (response.code !== "Success") {
        set({ error: response.msg, isLoading: false });
        return false;
      }

      // Store auth data
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
        set({ error: "Username and password are required", isLoading: false });
        return false;
      }

      // Call registration API using unified request entry
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
      // Call logout API
      await logoutApi();

      // Clear auth data
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
}));
