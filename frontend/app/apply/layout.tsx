import { Footer } from "@/components/common/footer";
import { NavBar } from "@/components/common/navbar";

export default function ApplyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col">
      <NavBar />
      <main className="flex flex-1 flex-col items-center justify-center bg-[#faf9f6] px-4 py-10 sm:px-6">
        {children}
      </main>
      <Footer />
    </div>
  );
}
