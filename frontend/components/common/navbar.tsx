import { DesktopNavBar } from "@/components/common/DesktopNavBar";
import { MobileNavBar } from "@/components/common/MobileNavBar";

export function NavBar() {
  return (
    <>
      <div className="block min-[780px]:hidden">
        <MobileNavBar />
      </div>
      <div className="hidden min-[780px]:block">
        <DesktopNavBar />
      </div>
    </>
  );
}
