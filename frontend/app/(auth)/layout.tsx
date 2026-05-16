import { Footer } from "@/components/common/footer";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col">
      <main className="flex flex-1 flex-col">{children}</main>
      <Footer />
    </div>
  );
}
