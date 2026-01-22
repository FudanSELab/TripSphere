import { get, post } from "@/lib/requests/base/request";
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from "@/lib/types";

export async function register(data: RegisterRequest) {
  return post<{ message?: string }>("/api/v1/users/register", data);
}

export async function login(credentials: LoginRequest) {
  return post<LoginResponse>("/api/v1/users/login", credentials);
}

export async function getCurrentUser() {
  // BFF will read token from cookie and validate
  return get<User>("/api/v1/users/current");
}

export async function logout() {
  return post<Record<string, never>>("/api/v1/users/logout", {});
}
