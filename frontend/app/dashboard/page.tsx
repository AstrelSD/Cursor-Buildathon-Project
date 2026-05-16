import {
  ArrowRight,
  Check,
  ImagePlus,
  Mic,
} from "lucide-react";
import CommonButton from "@/components/ui/button";
import { DASHBOARD_STEPS } from "@/constants/dashboardSteps";

export default function DashboardPage() {
  return (
    <div className="w-full max-w-5xl rounded-2xl border border-gray-100 bg-white shadow-xl">
        <header className="border-b border-gray-100 px-6 pb-6 pt-8 sm:px-10 sm:pt-10">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
            Apply for a Farm Loan
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-600 sm:text-base">
            Speak naturally to tell us what you need. Upload photos of your farm
            or documents to support your application.
          </p>
        </header>

        <div className="grid gap-8 p-6 sm:p-10 lg:grid-cols-2">
          <div className="space-y-6">
            <section className="rounded-xl border border-gray-100 bg-gray-50/50 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Tell us what you need
              </h2>
              <div className="mt-6 flex flex-col items-center text-center">
                <button
                  type="button"
                  className="flex h-20 w-20 items-center justify-center rounded-full bg-[#4CAF50] text-white shadow-lg shadow-green-200 transition-transform hover:scale-105 active:scale-95"
                  aria-label="Speak to apply"
                >
                  <Mic className="h-9 w-9" />
                </button>
                <p className="mt-4 font-semibold text-[#2E7D32]">
                  Speak to apply
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Tap the microphone and start talking.
                </p>
              </div>
            </section>

            <section className="rounded-xl border border-gray-100 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Add Photos or Documents
              </h2>
              <button
                type="button"
                className="mt-4 flex min-h-[160px] w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50/50 p-6 text-center transition-colors hover:border-[#4CAF50] hover:bg-green-50/30"
              >
                <ImagePlus className="h-10 w-10 text-gray-400" />
                <p className="mt-3 font-medium text-gray-700">
                  Tap here to add photos
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Upload pictures of your farm, equipment, or documents.
                </p>
              </button>
            </section>
          </div>

          <div className="flex flex-col">
            <section className="flex-1 rounded-xl border border-gray-100 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Application Status
              </h2>
              <ol className="mt-6 space-y-6">
                {DASHBOARD_STEPS.map((step) => (
                  <li key={step.id} className="flex gap-4">
                    {step.done ? (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#4CAF50] text-white">
                        <Check className="h-4 w-4" strokeWidth={3} />
                      </span>
                    ) : (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-gray-200 text-sm font-semibold text-gray-400">
                        {step.id}
                      </span>
                    )}
                    <div>
                      <p
                        className={
                          step.done
                            ? "font-medium text-[#2E7D32]"
                            : "font-medium text-gray-500"
                        }
                      >
                        {step.title}
                      </p>
                      <p className="mt-0.5 text-sm text-gray-400">
                        {step.status}
                      </p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>

            <div className="mt-6 lg:mt-8">
              <CommonButton
                type="button"
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#2E7D32] py-3.5 text-base font-medium text-white transition-colors hover:bg-[#1b5e20]"
                icon={<ArrowRight className="h-5 w-5" />}
                iconPosition="right"
              >
                Submit Application
              </CommonButton>
              <p className="mt-3 text-center text-xs text-gray-400">
                You can always add more information later.
              </p>
            </div>
          </div>
        </div>
    </div>
  );
}
