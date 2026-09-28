"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Eye, EyeOff, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

export default function LoginPage() {
  const router = useRouter();
  const { success, error: toastError } = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setErrorMessage("Please enter both your email address and password.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await api.login(email.trim(), password);
      // Store user metadata and JWT token in localStorage for API authentication
      if (typeof window !== "undefined") {
        localStorage.setItem("attendai_user", JSON.stringify(data.user));
        localStorage.setItem("attendai_token", data.access_token);
        // Set client-accessible auth cookie to coordinate with Next.js middleware
        document.cookie = `auth_token=${data.access_token}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
      }

      success(`Welcome back, ${data.user.full_name}!`);
      router.push("/");
      router.refresh();
    } catch (err: any) {
      setErrorMessage(
        err.message || "Invalid credentials. Please verify your email and password."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const setDemoCredentials = (role: "admin" | "teacher") => {
    if (role === "admin") {
      setEmail("ajeet.singh@kit.ac.in");
      setPassword("password123");
    } else {
      setEmail("ajeet.singh@kit.ac.in");
      setPassword("password123");
    }
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen w-full bg-canvas flex flex-col justify-center items-center p-4 selection:bg-accent/20">
      <div className="w-full max-w-sm space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-card bg-accent text-white mx-auto flex items-center justify-center shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h1 className="text-[22px] font-semibold text-primary-text tracking-tight">
            KIT Kanpur
          </h1>
          <p className="text-[13px] text-secondary-text">
            Kanpur Institute of Technology — Attendance Portal
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white border border-border rounded-card p-6 shadow-sm text-left">
          <form onSubmit={handleLogin} className="space-y-4">
            {errorMessage && (
              <div className="p-3 bg-danger-subtle border border-danger-border rounded-control text-danger text-[12.5px] flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span className="leading-snug">{errorMessage}</span>
              </div>
            )}

            <div>
              <Input
                label="Email Address"
                type="email"
                placeholder="ajeet.singh@kit.ac.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={<Mail className="w-4 h-4" />}
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-[13px] font-medium text-primary-text mb-1.5">
                Password
              </label>
              <div className="relative flex items-center">
                <Lock className="w-4 h-4 text-secondary-text absolute left-3 pointer-events-none" />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full h-9 bg-white text-primary-text text-[14px] placeholder:text-muted-text border border-border rounded-control pl-9 pr-9 transition-colors focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 p-1 text-secondary-text hover:text-primary-text"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full mt-2"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to KIT Kanpur Portal
            </Button>
          </form>

          {/* Quick Demo Credentials Switcher */}
          <div className="mt-5 pt-4 border-t border-border/80 text-[12px] text-secondary-text">
            <span className="block font-medium text-primary-text mb-2">
              Quick Demo Account:
            </span>
            <div>
              <button
                type="button"
                onClick={() => setDemoCredentials("admin")}
                className="w-full p-2.5 text-left bg-subtle border border-border rounded-control hover:border-accent hover:bg-accent-subtle/30 transition-colors"
              >
                <span className="font-semibold text-primary-text block text-[12px]">
                  Instructor & Administrator
                </span>
                <span className="text-[11px] text-secondary-text">Ajeet Singh • ajeet.singh@kit.ac.in</span>
              </button>
            </div>
          </div>
        </div>

        {/* Security & Privacy Footer */}
        <div className="text-center text-[11.5px] text-muted-text leading-relaxed">
          Protected with 512-bit vector encryption & audit-compliant logging.
        </div>
      </div>
    </div>
  );
}
