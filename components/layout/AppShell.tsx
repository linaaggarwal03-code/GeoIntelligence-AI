"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

interface AppShellProps {
  children: ReactNode;
}

const pageNames: Record<string, string> = {
  "/": "New Analysis",
  "/overview": "Overview",
  "/conflicts": "Conflicts",
  "/network": "Network",
  "/map": "Map",
  "/forecast": "Forecast",
  "/economic-impact": "Economic Impact",
  "/stock": "Stock Market AI",
  "/explainability": "Explainability",
  "/data-sources": "Data Sources",
  "/login": "Authentication Console",
};

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const activeItem = pageNames[pathname] ?? "GeoIntelligence AI";

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      // Open our sidebar when mouse enters the
      // first 70px INSIDE the webpage.
      if (event.clientX > 5 && event.clientX <= 70) {
        setSidebarOpen(true);
      }
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#edf2f6] dark:bg-[#0a0d14]">

      {/* Invisible application hover zone */}
      <div
        className="fixed left-0 top-0 z-[40] h-screen w-[70px]"
        onMouseEnter={() => setSidebarOpen(true)}
      />

      {/* Application Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onMouseEnter={() => setSidebarOpen(true)}
        onMouseLeave={() => setSidebarOpen(false)}
      />

      <div className="min-h-screen">
        <TopBar />

        <main className="min-h-[calc(100vh-76px)]">
          {children}
        </main>
      </div>
    </div>
  );
}