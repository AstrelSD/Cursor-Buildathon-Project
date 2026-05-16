import Link from "next/link";
import { AgriLendLogo } from "@/components/AgriLendLogo";

export function Footer() {
  return (
    <footer className="mt-auto shrink-0 border-t border-gray-100 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-6 text-sm text-gray-500 sm:flex-row sm:px-6 lg:px-8">
        <AgriLendLogo href="/" />

        <p className="text-center text-gray-500">
          © 2024 Agri-Lend. Empowering Agricultural Growth.
        </p>

        <div className="flex items-center gap-6">
          <Link
            href="#privacy"
            className="text-gray-500 transition-colors hover:text-[#2E7D32]"
          >
            Privacy Policy
          </Link>
          <Link
            href="#help"
            className="text-gray-500 transition-colors hover:text-[#2E7D32]"
          >
            Help Center
          </Link>
        </div>
      </div>
    </footer>
  );
}
