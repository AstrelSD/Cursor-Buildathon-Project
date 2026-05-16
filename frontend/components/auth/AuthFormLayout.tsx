import { AgriLendLogo } from "@/components/AgriLendLogo";

type AuthFormLayoutProps = {
  children: React.ReactNode;
  subtitle: string;
  maxWidth?: "md" | "lg";
};

export function AuthFormLayout({
  children,
  subtitle,
  maxWidth = "md",
}: AuthFormLayoutProps) {
  const widthClass = maxWidth === "lg" ? "max-w-lg" : "max-w-md";

  return (
    <div className="relative flex flex-1 flex-col">
      <div
        className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-[#4CAF50]/20 blur-3xl"
        aria-hidden
      />
      <div className="flex flex-1 flex-col items-center justify-center px-4 py-12">
        <div
          className={`w-full ${widthClass} rounded-2xl border border-gray-100 bg-white p-8 shadow-lg sm:p-10`}
        >
          <div className="flex flex-col items-center text-center">
            <AgriLendLogo href="/" />
            <p className="mt-4 text-sm text-gray-500">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
