"use client";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { useAuth } from "@/components/providers/AuthProvider";
import CommonButton from "@/components/ui/button";
import { PATH_DASHBOARD, PATH_LOGIN } from "@/constants/routes";

const navButtonBase =
  "shrink-0 rounded-lg px-4 py-2 text-sm font-medium sm:px-5";

type AuthNavActionsProps = {
  className?: string;
};

export function AuthNavActions({ className = "" }: AuthNavActionsProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <span
        className={`inline-block h-9 w-36 shrink-0 rounded-lg bg-gray-100 ${className}`}
        aria-hidden
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <CommonButton
        href={PATH_LOGIN}
        className={`${navButtonBase} bg-[#2E7D32] text-white transition-colors hover:bg-[#1b5e20] ${className}`}
      >
        Login
      </CommonButton>
    );
  }

  return (
    <div className={`flex shrink-0 items-center gap-2 sm:gap-3 ${className}`}>
      <CommonButton
        href={PATH_DASHBOARD}
        className={`${navButtonBase} border border-[#2E7D32] bg-white text-[#2E7D32] transition-colors hover:bg-green-50`}
      >
        Dashboard
      </CommonButton>
      <LogoutButton
        className={`${navButtonBase} bg-[#2E7D32] text-white transition-colors hover:bg-[#1b5e20]`}
      />
    </div>
  );
}
