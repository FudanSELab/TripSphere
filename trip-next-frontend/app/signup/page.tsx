"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SignupPage() {
  const router = useRouter();
  const auth = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState("");
  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  // Username validation: allows letters, numbers, and underscores
  const validateUsername = (value: string): string => {
    if (!value || value.trim() === "") {
      return "Please input username.";
    }
    if (!/^[a-zA-Z0-9_]+$/.test(value)) {
      return "Usernames can only contain letters, numbers, and underscores.";
    }
    return "";
  };

  // Password validation: at least 6 characters, only letters and numbers
  const validatePassword = (value: string): string => {
    if (value.length < 6) {
      return "Password must be at least 6 characters long.";
    }
    if (!/^[a-zA-Z0-9]+$/.test(value)) {
      return "Password can only contain letters and numbers.";
    }
    return "";
  };

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setUsername(value);
    if (usernameError) {
      setUsernameError(validateUsername(value));
    }
  };

  const handleUsernameBlur = () => {
    setUsernameError(validateUsername(username));
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    if (passwordError) {
      setPasswordError(validatePassword(value));
    }
  };

  const handlePasswordBlur = () => {
    setPasswordError(validatePassword(password));
  };

  const handleConfirmPasswordChange = (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const value = e.target.value;
    setConfirmPassword(value);
    if (confirmPasswordError && password) {
      setConfirmPasswordError(
        value !== password ? "Passwords do not match" : "",
      );
    }
  };

  const handleConfirmPasswordBlur = () => {
    if (confirmPassword && password !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
    } else {
      setConfirmPasswordError("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate username
    const usernameErr = validateUsername(username);
    if (usernameErr) {
      setUsernameError(usernameErr);
      return;
    }

    // Validate password
    const passwordErr = validatePassword(password);
    if (passwordErr) {
      setPasswordError(passwordErr);
      return;
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
      return;
    }

    if (!agreed) {
      setError("Please agree to the Terms of Service and Privacy Policy");
      return;
    }

    const success = await auth.register({ username, password });
    if (success) {
      router.push("/login");
    } else {
      setError(auth.error || "Registration failed. Please try again.");
    }
  };

  return (
    <div className="from-primary/5 to-secondary/5 via-background flex min-h-[calc(100vh-4rem)] items-center justify-center bg-linear-to-br px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex w-full max-w-md flex-col gap-6">
        <Card>
          <CardHeader className="text-center">
            <div className="bg-primary text-primary-foreground mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-2xl text-xl font-bold">
              T
            </div>
            <CardTitle className="text-2xl">Create Account</CardTitle>
            <CardDescription>
              Join TripSphere and start planning your perfect trip
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <FieldGroup>
                {error && (
                  <div className="border-destructive/20 bg-destructive/10 text-destructive flex items-center gap-2 rounded-lg border p-4 text-sm">
                    <AlertCircle className="h-5 w-5 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <Field>
                  <FieldLabel htmlFor="username">Username</FieldLabel>
                  <Input
                    id="username"
                    type="text"
                    value={username}
                    onChange={handleUsernameChange}
                    onBlur={handleUsernameBlur}
                    placeholder="Choose a username"
                    required
                    aria-invalid={!!usernameError}
                  />
                  {usernameError && <FieldError>{usernameError}</FieldError>}
                </Field>

                <Field>
                  <div className="grid grid-cols-2 gap-4">
                    <Field>
                      <FieldLabel htmlFor="password">Password</FieldLabel>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={handlePasswordChange}
                        onBlur={handlePasswordBlur}
                        placeholder="Create password"
                        required
                        aria-invalid={!!passwordError}
                      />
                      {passwordError && (
                        <FieldError>{passwordError}</FieldError>
                      )}
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="confirm-password">
                        Confirm
                      </FieldLabel>
                      <Input
                        id="confirm-password"
                        type="password"
                        value={confirmPassword}
                        onChange={handleConfirmPasswordChange}
                        onBlur={handleConfirmPasswordBlur}
                        placeholder="Confirm password"
                        required
                        aria-invalid={!!confirmPasswordError}
                      />
                      {confirmPasswordError && (
                        <FieldError>{confirmPasswordError}</FieldError>
                      )}
                    </Field>
                  </div>
                  <FieldDescription>
                    Must be at least 6 characters, letters and numbers only.
                  </FieldDescription>
                </Field>

                <Field orientation="horizontal" className="!items-start">
                  <Checkbox
                    id="terms"
                    checked={agreed}
                    onCheckedChange={(checked) => setAgreed(checked === true)}
                    className="mt-1"
                  />
                  <FieldLabel
                    htmlFor="terms"
                    className="cursor-pointer text-sm leading-normal font-normal"
                  >
                    I agree to the{" "}
                    <Link
                      href="/terms"
                      className="text-primary hover:text-primary/80 underline-offset-4 hover:underline"
                    >
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link
                      href="/privacy"
                      className="text-primary hover:text-primary/80 underline-offset-4 hover:underline"
                    >
                      Privacy Policy
                    </Link>
                  </FieldLabel>
                </Field>

                <Field>
                  <Button type="submit" className="w-full" size="lg">
                    Create Account
                  </Button>
                  <FieldDescription className="text-center">
                    Already have an account?{" "}
                    <Link
                      href="/login"
                      className="text-primary hover:text-primary/80 font-medium underline-offset-4 hover:underline"
                    >
                      Sign in
                    </Link>
                  </FieldDescription>
                </Field>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
