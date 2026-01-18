import { post } from "@/lib/requests/base/request";
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from "@/lib/types";

export async function register(data: RegisterRequest) {
  return post<{ message?: string }>("/api/v1/user/register", data);
}

export async function login(credentials: LoginRequest) {
  return post<LoginResponse>("/api/v1/user/login", credentials);
}

export async function getCurrentUser() {
  // BFF will read token from cookie and validate
  return post<User>("/api/v1/user/get-current-user", undefined);
}

export async function changePassword(data: {
  username: string;
  oldPassword: string;
  newPassword: string;
}) {
  return post<{ message?: string }>("/api/v1/user/change-password", data);
}

export async function logout() {
  return post<Record<string, never>>("/api/v1/user/logout", {});
}
