import type { Metadata } from "next";
import { SigninForm } from "@/components/signin-form";

export const metadata: Metadata = {
  title: "登录",
};

export default function SignInPage() {
  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <SigninForm />
      </div>
    </div>
  );
}
