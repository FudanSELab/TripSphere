import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from "@/lib/types";
import { post } from "../base/request";

export async function register(data: RegisterRequest) {
  return post<{ message?: string }>("/api/user/register", data);
}

export async function login(credentials: LoginRequest) {
  return post<LoginResponse>("/api/user/login", credentials);
}

export async function getCurrentUser(token?: string | null) {
  return post<User>("/api/user/get-current-user", undefined);
}

export async function changePassword(data: {
  username: string;
  oldPassword: string;
  newPassword: string;
}) {
  return post<{ message?: string }>("/api/user/change-password", data);
}

export async function logout() {
  return post<{}>("/api/user/logout", {});
}
