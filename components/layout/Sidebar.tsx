"use client";

import {
  Activity,
  BarChart3,
  CandlestickChart,
  LayoutDashboard,
  Map,
  Network,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  UserCheck,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

interface SidebarProps {
  isOpen: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

const navigation = [
  {
    label: "New Analysis",
    icon: Sparkles,
    path: "/",
  },
  {
    label: "Overview",
    icon: LayoutDashboard,
    path: "/overview",
  },
  {
    label: "Conflicts",
    icon: ShieldAlert,
    path: "/conflicts",
  },
  {
    label: "Network",
    icon: Network,
    path: "/network",
  },
  {
    label: "Map",
    icon: Map,
    path: "/map",
  },
  {
    label: "Forecast",
    icon: TrendingUp,
    path: "/forecast",
  },
  {
    label: "Economic Impact",
    icon: BarChart3,
    path: "/economic-impact",
  },
  {
    label: "Stock Market AI",
    icon: CandlestickChart,
    path: "/stock",
  },
  {
    label: "Explainability",
    icon: Activity,
    path: "/explainability",
  },
];

export default function Sidebar({
  isOpen,
  onMouseEnter,
  onMouseLeave,
}: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();

  const initials = user?.name
    ? user.name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((n) => n[0].toUpperCase())
        .join("")
    : "AI";

  return (
    <aside
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className={`fixed left-0 top-0 z-[600] flex h-screen w-[255px] flex-col border-r border-white/10 bg-[#172235] text-slate-300 shadow-2xl transition-transform duration-300 ease-out ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Logo */}
      <div className="flex h-[76px] shrink-0 items-center justify-center border-b border-white/10">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-md shadow-blue-900/30">
          <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <ellipse cx="12" cy="12" rx="4.5" ry="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <line x1="3" y1="12" x2="21" y2="12" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <line x1="5" y1="7" x2="19" y2="7" stroke="white" strokeWidth="1.2" strokeOpacity="0.4" />
            <line x1="5" y1="17" x2="19" y2="17" stroke="white" strokeWidth="1.2" strokeOpacity="0.4" />
            <circle cx="12" cy="12" r="1.8" fill="white" />
          </svg>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-5">
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          Workspace
        </p>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;

            const isActive =
              pathname === item.path ||
              (item.path !== "/" && pathname.startsWith(item.path));

            return (
              <button
                key={item.label}
                onClick={() => router.push(item.path)}
                className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] transition-all ${
                  isActive
                    ? "bg-blue-500/15 text-blue-300 shadow-sm"
                    : "text-slate-400 hover:bg-white/[0.05] hover:text-slate-200"
                }`}
              >
                <Icon
                  className={`h-[17px] w-[17px] shrink-0 ${
                    isActive
                      ? "text-blue-400"
                      : "text-slate-500 group-hover:text-slate-300"
                  }`}
                  strokeWidth={1.8}
                />

                <span>{item.label}</span>

                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom User Account Status Widget */}
      <div className="border-t border-white/10 p-3">
        {isAuthenticated && user ? (
          <button
            onClick={() => router.push("/login")}
            className="flex w-full items-center gap-3 rounded-xl bg-white/[0.04] p-2.5 text-left transition hover:bg-white/[0.08]"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-xs font-bold text-white shadow-sm">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-white">
                {user.name}
              </p>
            </div>
            <UserCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          </button>
        ) : (
          <button
            onClick={() => router.push("/login")}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
          >
            Sign In / Register
          </button>
        )}
      </div>
    </aside>
  );
}