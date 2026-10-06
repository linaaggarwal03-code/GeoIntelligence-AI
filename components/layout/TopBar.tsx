"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  ChevronDown,
  LogOut,
  Moon,
  Sun,
  User,
  LogIn,
  KeyRound,
  ExternalLink,
} from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";

export default function TopBar() {
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const isDark = theme === "dark";

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Compute initials from name
  const initials = user?.name
    ? user.name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((n) => n[0].toUpperCase())
        .join("")
    : "AI";

  return (
    <header className="relative z-[500] flex h-[76px] shrink-0 items-center justify-between border-b border-slate-200 bg-[#f4f7fa] px-7 dark:border-slate-800 dark:bg-[#0f1117]">
      {/* Brand Lockup */}
      <Link href="/" className="flex items-center gap-3 transition hover:opacity-90">
        {/* Logo Mark */}
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-md shadow-blue-900/20">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <ellipse cx="12" cy="12" rx="4.5" ry="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <line x1="3" y1="12" x2="21" y2="12" stroke="white" strokeWidth="1.4" strokeOpacity="0.6" />
            <line x1="5" y1="7" x2="19" y2="7" stroke="white" strokeWidth="1.2" strokeOpacity="0.4" />
            <line x1="5" y1="17" x2="19" y2="17" stroke="white" strokeWidth="1.2" strokeOpacity="0.4" />
            <circle cx="12" cy="12" r="1.8" fill="white" />
          </svg>
        </div>

        {/* Wordmark */}
        <div>
          <p className="text-[14px] font-bold tracking-wide text-slate-800 dark:text-slate-100">
            GEOINTELLIGENCE <span className="text-blue-600 dark:text-blue-400">AI</span>
          </p>
          <p className="text-[9px] font-medium uppercase tracking-[0.22em] text-slate-400">
            Conflict · Economy · Energy · Global Impact
          </p>
        </div>
      </Link>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button
          aria-label="Notifications"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-blue-500 ring-2 ring-white dark:ring-slate-800" />
        </button>

        {/* Day / Dark Theme Toggle */}
        <button
          onClick={toggleTheme}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className="relative flex h-9 w-[64px] items-center rounded-full border border-slate-200 bg-white px-1 shadow-sm transition hover:border-slate-300 dark:border-slate-800 dark:bg-slate-800 dark:hover:border-slate-700"
        >
          <Sun className="h-3.5 w-3.5 shrink-0 text-amber-400" />
          <Moon className="ml-auto h-3.5 w-3.5 shrink-0 text-slate-400 dark:text-blue-400" />

          {/* Sliding pill */}
          <span
            className={`absolute top-[3px] h-[26px] w-[26px] rounded-full shadow-sm transition-all duration-300 ${
              isDark
                ? "left-[33px] bg-slate-700"
                : "left-[3px] bg-amber-50 border border-amber-200"
            }`}
          />
        </button>

        {/* Profile / Authentication Menu */}
        {isAuthenticated && user ? (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700"
            >
              {/* Avatar circle */}
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-[10px] font-bold text-white shadow-sm">
                {initials}
              </div>

              <div className="hidden text-left sm:block max-w-[130px]">
                <p className="truncate text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                  {user.name}
                </p>
              </div>

              <ChevronDown
                className={`h-3.5 w-3.5 text-slate-400 transition-transform ${
                  dropdownOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Profile Dropdown Card */}
            {dropdownOpen && (
              <div className="absolute right-0 top-12 z-50 w-64 rounded-2xl border border-slate-200 bg-white p-3.5 shadow-2xl transition dark:border-slate-800 dark:bg-[#111622]">
                {/* Header with user details */}
                <div className="flex items-center gap-3 pb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-xs font-bold text-white shadow-md">
                    {initials}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-bold text-slate-900 dark:text-white">
                      {user.name}
                    </p>
                    <p className="truncate text-[10px] text-slate-400 font-mono">
                      {user.email}
                    </p>
                  </div>
                </div>

                {/* Menu Actions */}
                <div className="space-y-1 pt-1 border-t border-slate-100 dark:border-slate-800">
                  <Link
                    href="/login"
                    onClick={() => setDropdownOpen(false)}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    <KeyRound className="h-3.5 w-3.5 text-blue-500" />
                    Switch / Change Account
                  </Link>

                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
          >
            <LogIn className="h-3.5 w-3.5" />
            Sign In
          </Link>
        )}
      </div>
    </header>
  );
}