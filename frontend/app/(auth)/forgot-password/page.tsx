"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Eye, EyeOff, Lock, User } from "lucide-react";
import { AgriLendLogo } from "@/app/components/AgriLendLogo";
import { Footer } from "../../components/common/footer";

export default function ForgotPasswordPage() {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative flex min-h-full flex-1 flex-col">
      <div
        className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-[#4CAF50]/20 blur-3xl"
        aria-hidden
      />

      <div className="flex flex-1 flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-gray-100 bg-white p-8 shadow-lg sm:p-10">
          <div className="flex flex-col items-center text-center">
            <AgriLendLogo href="/" />
            <p className="mt-4 text-sm text-gray-500">
              Secure access to your farm&apos;s financial future.
            </p>
          </div>

          <form
            className="mt-8 space-y-5"
            onSubmit={(e) => e.preventDefault()}
          >
            <div>
              <label
                htmlFor="identifier"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Phone Number or Email
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  id="identifier"
                  type="text"
                  placeholder="Enter phone or email"
                  className="w-full rounded-lg border border-gray-200 py-3 pl-10 pr-4 text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-[#2E7D32] focus:ring-2 focus:ring-[#2E7D32]/20"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                PIN or Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your PIN or password"
                  className="w-full rounded-lg border border-gray-200 py-3 pl-10 pr-12 text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-[#2E7D32] focus:ring-2 focus:ring-[#2E7D32]/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#2E7D32] py-3.5 text-base font-medium text-white transition-colors hover:bg-[#1b5e20]"
            >
              Log In
              <ArrowRight className="h-5 w-5" />
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            <Link href="#help" className="hover:text-[#2E7D32]">
              Need help signing in?
            </Link>
          </p>

          <p className="mt-8 border-t border-gray-100 pt-6 text-center text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <Link
              href="/apply"
              className="font-medium text-[#2E7D32] hover:underline"
            >
              Apply for a Loan
            </Link>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  );
}
