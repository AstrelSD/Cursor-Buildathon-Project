import { Footer } from "@/components/common/footer";
import { NavBar } from "@/components/common/navbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col">
      <NavBar />
      <main className="flex flex-1 flex-col bg-[#f8faf8] px-4 py-6 sm:px-6 sm:py-10">
        {children}
      </main>
      <Footer />
    </div>
  );
}
