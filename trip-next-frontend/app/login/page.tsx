"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const auth = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");

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
    setUsernameError(validateUsername(value));
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    setPasswordError(validatePassword(value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate username and password
    const usernameErr = validateUsername(username);
    const passwordErr = validatePassword(password);

    setUsernameError(usernameErr);
    setPasswordError(passwordErr);

    // If validation errors exist, do not proceed with login
    if (usernameErr || passwordErr) {
      return;
    }

    const success = await auth.login({ username, password });
    if (success) {
      router.push("/");
    } else {
      setError(auth.error || "Login failed. Please try again.");
    }
  };

  return (
    <div className="from-primary/5 to-secondary/5 via-background flex min-h-screen items-center justify-center bg-linear-to-br px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="bg-primary text-primary-foreground mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl text-2xl font-bold">
            T
          </div>
          <h2 className="text-foreground text-3xl font-bold">Welcome Back</h2>
          <p className="text-muted-foreground mt-2">
            Sign in to your TripSphere account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="border-destructive/20 bg-destructive/10 text-destructive flex items-center gap-2 rounded-lg border p-4 text-sm">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Input
            type="text"
            value={username}
            onChange={handleUsernameChange}
            placeholder="Enter your username"
            required
          />

          <Input
            type="password"
            value={password}
            onChange={handlePasswordChange}
            placeholder="Enter your password"
            required
          />

          <Button type="submit" className="w-full" size="lg">
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-muted-foreground text-sm">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-primary hover:text-primary/80 font-medium"
            >
              Sign up for free
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}
