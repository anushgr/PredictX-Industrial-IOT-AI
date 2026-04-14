"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useDashboardStore } from "@/store/use-dashboard-store";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isSidebarCollapsed } = useDashboardStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (pathname !== "/login") {
      const token = localStorage.getItem("predictx_token");
      if (!token) {
        router.replace("/login");
      }
    }
  }, [pathname, router]);

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.08),_transparent_40%),linear-gradient(135deg,#020617_20%,#0b1220_60%,#111827_100%)] text-slate-100">
      <Sidebar />
      <div
        className={cn(
          "transition-all duration-300 lg:pl-72",
          isSidebarCollapsed && "lg:pl-24",
        )}
      >
        <Header />
        <main className="min-h-[calc(100vh-64px)] px-4 py-5 sm:px-6">{children}</main>
        <Footer />
      </div>
    </div>
  );
}
