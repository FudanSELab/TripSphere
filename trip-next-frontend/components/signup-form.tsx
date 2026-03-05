"use client";

import { signUp } from "@/actions/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldError,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useActionState } from "react";

export function SignupForm({ ...props }: React.ComponentProps<typeof Card>) {
  const [state, action, pending] = useActionState(signUp, undefined);

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>创建账户</CardTitle>
        <CardDescription>请输入您的信息以创建账户</CardDescription>
      </CardHeader>
      <CardContent>
        <form action={action}>
          <FieldGroup>
            <Field data-invalid={!!state?.errors?.name?.length}>
              <FieldLabel htmlFor="name">姓名</FieldLabel>
              <Input
                id="name"
                name="name"
                type="text"
                required
                aria-invalid={!!state?.errors?.name?.length}
              />
              {state?.errors?.name && (
                <FieldError>{state.errors.name[0]}</FieldError>
              )}
            </Field>

            <Field data-invalid={!!state?.errors?.email?.length}>
              <FieldLabel htmlFor="email">邮箱</FieldLabel>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="email@example.com"
                required
                aria-invalid={!!state?.errors?.email?.length}
              />
              <FieldDescription>
                该邮箱仅用于与您联系，不会与任何人分享。
              </FieldDescription>
              {state?.errors?.email && (
                <FieldError>{state.errors.email[0]}</FieldError>
              )}
            </Field>

            <Field data-invalid={!!state?.errors?.password?.length}>
              <FieldLabel htmlFor="password">密码</FieldLabel>
              <Input
                id="password"
                name="password"
                type="password"
                required
                aria-invalid={!!state?.errors?.password?.length}
              />
              <FieldDescription>密码长度至少为 8 个字符。</FieldDescription>
              {state?.errors?.password && (
                <FieldError>{state.errors.password[0]}</FieldError>
              )}
            </Field>

            <Field data-invalid={!!state?.errors?.confirmPassword?.length}>
              <FieldLabel htmlFor="confirmPassword">确认密码</FieldLabel>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                aria-invalid={!!state?.errors?.confirmPassword?.length}
              />
              <FieldDescription>请再次输入您的密码。</FieldDescription>
              {state?.errors?.confirmPassword && (
                <FieldError>{state.errors.confirmPassword[0]}</FieldError>
              )}
            </Field>

            {state?.message && (
              <p className="text-destructive text-sm">{state.message}</p>
            )}

            <FieldGroup>
              <Field>
                <Button type="submit" disabled={pending}>
                  创建账户
                </Button>
                <Button variant="outline" type="button">
                  使用 Google 注册
                </Button>
                <FieldDescription className="px-6 text-center">
                  已有账户？<a href="/signin">登录</a>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
