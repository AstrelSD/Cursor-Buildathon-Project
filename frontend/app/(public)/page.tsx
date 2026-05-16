import { Leaf } from "lucide-react";
import LandingBanner from "../components/home/landingBanner";
import ProcessCard from "../components/home/processCard";
import { STEPS } from "../constants/home";

export default function HomePage() {
  return (
    <>
      <div className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute -right-24 top-8 h-[420px] w-[420px] opacity-[0.12]"
          aria-hidden
        >
          <Leaf
            className="h-full w-full text-[#4CAF50]"
            strokeWidth={0.75}
            fill="currentColor"
          />
        </div>
        <LandingBanner />
      </div>

      <div
        id="how-it-works"
        className="border-t border-gray-100 bg-white/60 py-20"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">
              How it Works
            </h2>
            <p className="mt-3 text-lg text-gray-600">
              Three simple steps to secure your farm&apos;s future.
            </p>
          </div>

          <div className="mt-14 grid gap-8 md:grid-cols-3">
            {STEPS.map((step, index) => (
              <ProcessCard
                key={step.title}
                step={step}
                index={index}
              />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}


