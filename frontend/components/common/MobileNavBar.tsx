"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { AuthNavActions } from "@/components/auth/AuthNavActions";
import { AgriLendLogo } from "@/components/AgriLendLogo";
import { NAV_LINKS } from "@/constants/home";

export function MobileNavBar() {
  const [open, setOpen] = useState(false);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, close]);

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-gray-100/80 bg-white/90 backdrop-blur-sm">
        <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
          <AgriLendLogo />

          <button
            type="button"
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-gray-700 transition-colors hover:bg-gray-100 hover:text-[#2E7D32]"
            onClick={() => setOpen(true)}
            aria-expanded={open}
            aria-controls="mobile-nav-menu"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>
      </header>

      {open ? (
        <div
          id="mobile-nav-menu"
          className="fixed inset-0 z-[60] flex min-h-dvh w-full flex-col bg-white"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
        >
          <div className="flex h-16 shrink-0 items-center justify-between border-b border-gray-100 px-4 sm:px-6">
            <AgriLendLogo />
            <button
              type="button"
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-gray-700 transition-colors hover:bg-gray-100 hover:text-[#2E7D32]"
              onClick={close}
              aria-label="Close menu"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <nav
            className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6"
            aria-label="Main"
          >
            <ul className="flex flex-col gap-1">
              {NAV_LINKS.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="block rounded-lg px-3 py-3 text-base font-medium text-gray-700 transition-colors hover:bg-green-50 hover:text-[#2E7D32]"
                    onClick={close}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="mt-auto border-t border-gray-100 pt-6">
              <AuthNavActions className="w-full justify-center" />
            </div>
          </nav>
        </div>
      ) : null}
    </>
  );
}
