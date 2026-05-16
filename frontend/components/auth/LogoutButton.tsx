"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import CommonButton from "@/components/ui/button";
import { PATH_LOGIN } from "@/constants/routes";
import { createClient } from "@/lib/supabase/client";
import { signOut } from "@/utils/authFunctions";

type LogoutButtonProps = {
  className?: string;
};

export function LogoutButton({ className }: LogoutButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleLogout = async () => {
    setLoading(true);
    try {
      await signOut();
      router.push(PATH_LOGIN);
      router.refresh();
    } finally {
      setLoading(false);
    }
  };

  return (
    <CommonButton
      type="button"
      onClick={handleLogout}
      loading={loading}
      className={
        className ??
        "shrink-0 rounded-lg border border-gray-200 bg-white px-5 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
      }
    >
      Logout
    </CommonButton>
  );
}

export function NavAuthButton() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      setIsLoggedIn(!!session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setIsLoggedIn(!!session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (isLoggedIn === null) {
    return (
      <span
        className="inline-block h-9 w-20 shrink-0 rounded-lg bg-gray-100"
        aria-hidden
      />
    );
  }

  if (isLoggedIn) {
    return (
      <LogoutButton className="shrink-0 rounded-lg bg-[#2E7D32] px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-[#1b5e20]" />
    );
  }

  return (
    <CommonButton
      href={PATH_LOGIN}
      className="shrink-0 rounded-lg bg-[#2E7D32] px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-[#1b5e20]"
    >
      Login
    </CommonButton>
  );
}
