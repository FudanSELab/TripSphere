"use server";

import * as z from "zod";
import { redirect } from "next/navigation";
import { status as grpcStatus } from "@grpc/grpc-js";
import {
  SignUpFormSchema,
  SignInFormSchema,
  SignUpFormState,
  SignInFormState,
} from "@/lib/definitions";
import { createSession, deleteSession } from "@/lib/session";
import { getUserService } from "@/lib/grpc/client";
import type { SignInResponse } from "@/lib/grpc/generated/tripsphere/user/v1/user";

const SIGN_UP_ERROR_MESSAGES: Partial<Record<number, string>> = {
  [grpcStatus.ALREADY_EXISTS]: "该邮箱已被注册。",
  [grpcStatus.INVALID_ARGUMENT]: "输入信息无效，请检查后重试。",
};

const SIGN_IN_ERROR_MESSAGES: Partial<Record<number, string>> = {
  [grpcStatus.UNAUTHENTICATED]: "邮箱或密码错误。",
  [grpcStatus.NOT_FOUND]: "邮箱或密码错误。",
  [grpcStatus.INVALID_ARGUMENT]: "输入信息无效，请检查后重试。",
};

export async function signUp(
  state: SignUpFormState,
  formData: FormData,
): Promise<SignUpFormState> {
  const validatedFields = SignUpFormSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
    confirmPassword: formData.get("confirmPassword"),
  });

  if (!validatedFields.success) {
    return {
      errors: z.flattenError(validatedFields.error).fieldErrors,
    };
  }

  const { name, email, password } = validatedFields.data;
  const client = getUserService();

  try {
    await new Promise<void>((resolve, reject) => {
      client.signUp({ name, email, password }, (error) => {
        if (error) reject(error);
        else resolve();
      });
    });
  } catch (error: unknown) {
    const code = (error as { code?: number }).code;

    return {
      message:
        (code != null && SIGN_UP_ERROR_MESSAGES[code]) ||
        "注册失败，请稍后再试。",
    };
  }

  redirect("/signin");
}

export async function signIn(
  state: SignInFormState,
  formData: FormData,
): Promise<SignInFormState> {
  const validatedFields = SignInFormSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  if (!validatedFields.success) {
    return {
      errors: z.flattenError(validatedFields.error).fieldErrors,
    };
  }

  const { email, password } = validatedFields.data;
  const client = getUserService();

  try {
    const response = await new Promise<SignInResponse>((resolve, reject) => {
      client.signIn({ email, password }, (error, response) => {
        if (error) reject(error);
        else resolve(response);
      });
    });

    await createSession(response.token);
  } catch (error: unknown) {
    const code = (error as { code?: number }).code;

    return {
      message:
        (code != null && SIGN_IN_ERROR_MESSAGES[code]) ||
        "登录失败，请稍后再试。",
    };
  }

  redirect("/");
}

export async function signOut() {
  await deleteSession();
  redirect("/signin");
}
