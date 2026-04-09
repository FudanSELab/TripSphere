import * as z from "zod";

export const SignUpFormSchema = z
  .object({
    name: z.string().min(2, { error: "姓名至少需要2个字符。" }).trim(),
    email: z.email({ error: "请输入有效的邮箱。" }).trim(),
    password: z
      .string()
      .min(8, { error: "密码至少需要8个字符。" })
      .regex(/[a-zA-Z]/, { error: "密码至少需要包含一个字母。" })
      .regex(/[0-9]/, { error: "密码至少需要包含一个数字。" })
      .regex(/[^a-zA-Z0-9]/, {
        error: "密码至少需要包含一个特殊字符。",
      })
      .trim(),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "两次输入的密码不一致。",
    path: ["confirmPassword"],
  });

export const SignInFormSchema = z.object({
  email: z.email({ error: "请输入有效的邮箱。" }).trim(),
  password: z.string().min(8, { error: "密码至少需要8个字符。" }).trim(),
});

export type SignUpFormState =
  | {
      errors?: Partial<
        Record<keyof z.input<typeof SignUpFormSchema>, string[]>
      >;
      message?: string;
    }
  | undefined;

export type SignInFormState =
  | {
      errors?: Partial<
        Record<keyof z.input<typeof SignInFormSchema>, string[]>
      >;
      message?: string;
    }
  | undefined;

export type SessionPayload = {
  userId: string;
  name: string;
  email: string;
  roles: string[];
  expiresAt: Date; // mapped from JWT exp (unix seconds -> Date)
};
