"use client";

import { useAuth } from "@/hooks/use-auth";
import { useEffect } from "react";

/**
 * AuthProvider - Handles authentication initialization
 *
 * This component initializes the authentication state by checking
 * if the user has a valid session cookie. It runs once on mount.
 *
 * Architecture:
 * - Cookie-based authentication managed by BFF
 * - BFF reads token from cookie and validates
 * - Frontend stores only user info, not token
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const initAuth = useAuth((state) => state.initAuth);

  useEffect(() => {
    // Initialize auth state on mount
    // This will check if user has valid session cookie
    initAuth();
  }, [initAuth]);

  return <>{children}</>;
}
