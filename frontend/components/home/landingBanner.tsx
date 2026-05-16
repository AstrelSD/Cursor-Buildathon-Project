import CommonButton from "@/components/ui/button";
import { PATH_DASHBOARD } from "@/constants/routes";

const outlineClassName =
  "inline-flex items-center justify-center rounded-lg border-2 border-[#2E7D32] bg-white px-8 py-3.5 text-base font-medium text-[#2E7D32] transition-colors hover:bg-green-50";

export default function LandingBanner() {
  return (
    <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8 lg:py-28">
      <div className="max-w-2xl">
        <h1 className="font-serif text-4xl font-bold leading-tight tracking-tight text-[#1b5e20] sm:text-5xl lg:text-6xl">
          Financial Growth for Every Acre
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-gray-600">
          Simple, fast, and fair agricultural lending built specifically for
          the needs of modern farmers. Apply in minutes, get approved in hours.
        </p>
        <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
          <CommonButton href={PATH_DASHBOARD}>Get Started</CommonButton>
          <CommonButton href="#how-it-works" className={outlineClassName}>
            View Loan Options
          </CommonButton>
        </div>
      </div>
    </div>
  );
}
