import { FallingLeavesBanner } from "@/components/common/FallingLeavesBanner";
import { Footer } from "@/components/common/footer";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col">
      <FallingLeavesBanner className="flex min-h-0 w-full flex-1 flex-col">
        <main className="flex flex-1 flex-col">{children}</main>
      </FallingLeavesBanner>
      <Footer />
    </div>
  );
}
