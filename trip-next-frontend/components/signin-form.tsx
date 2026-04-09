"use client";

import Link from "next/link";
import { signIn } from "@/actions/auth";
import { cn } from "@/lib/utils";
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
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useActionState } from "react";

export function SigninForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [state, action, pending] = useActionState(signIn, undefined);

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>登录您的账户</CardTitle>
          <CardDescription>请输入您的邮箱以登录账户</CardDescription>
        </CardHeader>
        <CardContent>
          <form action={action}>
            <FieldGroup>
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
                {state?.errors?.email && (
                  <FieldError>{state.errors.email[0]}</FieldError>
                )}
              </Field>
              <Field data-invalid={!!state?.errors?.password?.length}>
                <div className="flex items-center">
                  <FieldLabel htmlFor="password">密码</FieldLabel>
                  <a
                    href="#"
                    className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                  >
                    忘记密码？
                  </a>
                </div>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  aria-invalid={!!state?.errors?.password?.length}
                />
                {state?.errors?.password && (
                  <FieldError>{state.errors.password[0]}</FieldError>
                )}
              </Field>

              {state?.message && (
                <p className="text-destructive text-sm">{state.message}</p>
              )}

              <Field>
                <Button type="submit" disabled={pending}>
                  登录
                </Button>
                <Button variant="outline" type="button">
                  使用 Google 登录
                </Button>
                <FieldDescription className="text-center">
                  还没有账户？<Link href="/signup">注册</Link>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
