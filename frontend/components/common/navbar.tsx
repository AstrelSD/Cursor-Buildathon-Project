import Link from "next/link";
import { NavAuthButton } from "@/components/auth/LogoutButton";
import { AgriLendLogo } from "../AgriLendLogo";
import { NAV_LINKS } from "@/constants/home";

export function NavBar() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-100/80 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6 lg:px-8">
        <AgriLendLogo />

        <nav className="hidden items-center gap-8 md:flex" aria-label="Main">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-gray-600 transition-colors hover:text-[#2E7D32]"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <NavAuthButton />
      </div>
    </header>
  );
}
