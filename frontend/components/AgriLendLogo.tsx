import { Leaf } from "lucide-react";
import Link from "next/link";

type AgriLendLogoProps = {
  href?: string;
  className?: string;
};

export function AgriLendLogo({ href = "/", className = "" }: AgriLendLogoProps) {
  const content = (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#4CAF50]">
        <Leaf className="h-4 w-4 text-white" strokeWidth={2.5} />
      </span>
      <span className="text-lg font-semibold tracking-tight text-[#2E7D32]">
        Agri-Lend
      </span>
    </span>
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex shrink-0">
        {content}
      </Link>
    );
  }

  return content;
}
