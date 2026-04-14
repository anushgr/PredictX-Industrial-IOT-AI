"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Gauge,
  LogOut,
  Settings,
  Shield,
  Users,
  Wrench,
  X,
} from "lucide-react";
import { motion } from "framer-motion";
import { useDashboardStore } from "@/store/use-dashboard-store";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const navItems = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/live-monitoring", label: "Live Monitoring", icon: Activity },
  { href: "/machines", label: "Machines", icon: Wrench },
  { href: "/predictive-alerts", label: "Predictive Alerts", icon: AlertTriangle },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/users", label: "Users & Roles", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    isSidebarCollapsed,
    toggleSidebar,
    isMobileSidebarOpen,
    setMobileSidebarOpen,
  } = useDashboardStore();

  return (
    <>
      {isMobileSidebarOpen && (
        <button
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          aria-label="Close sidebar backdrop"
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-slate-800/90 bg-slate-950/90 px-4 pb-4 pt-5 backdrop-blur-xl transition-transform lg:translate-x-0",
          isSidebarCollapsed && "lg:w-24",
          isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="mb-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-300">
              <Shield className="h-5 w-5" />
            </div>
            {!isSidebarCollapsed && (
              <div>
                <p className="text-sm font-semibold text-slate-200">PredictX Industrial AI</p>
                <Badge className="mt-1 border-emerald-500/30 bg-emerald-500/15 text-emerald-300">
                  System Online
                </Badge>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              if (window.innerWidth < 1024) setMobileSidebarOpen(false);
              else toggleSidebar();
            }}
          >
            <X className="h-4 w-4 text-slate-400" />
          </Button>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <motion.div
                  whileHover={{ x: 2 }}
                  className={cn(
                    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                    active
                      ? "bg-cyan-500/20 text-cyan-200"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-100",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {!isSidebarCollapsed && <span>{item.label}</span>}
                </motion.div>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900/80 p-3">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 rounded-full">
              <AvatarFallback>AT</AvatarFallback>
            </Avatar>
            {!isSidebarCollapsed && (
              <div>
                <p className="text-sm font-medium text-slate-100">Ava Thompson</p>
                <Badge className="border-cyan-500/30 bg-cyan-500/15 text-cyan-300">Admin</Badge>
              </div>
            )}
          </div>
          {!isSidebarCollapsed && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3 w-full justify-start"
              onClick={() => {
                localStorage.removeItem("predictx_token");
                toast.success("Signed out");
                router.push("/login");
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          )}
        </div>
      </aside>
    </>
  );
}
