import type { LucideIcon } from "lucide-react";

type Step = {
  icon: LucideIcon;
  title: string;
  description: string;
};

type ProcessCardProps = {
  step: Step;
  index: number;
};

export default function ProcessCard({ step, index }: ProcessCardProps) {
  const Icon = step.icon;

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-50 text-[#2E7D32]">
        <Icon className="h-6 w-6" />
      </div>
      <p className="mt-4 text-sm font-semibold text-[#4CAF50]">
        Step {index + 1}
      </p>
      <h3 className="mt-2 text-lg font-semibold text-gray-900">{step.title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-gray-600">
        {step.description}
      </p>
    </div>
  );
}
