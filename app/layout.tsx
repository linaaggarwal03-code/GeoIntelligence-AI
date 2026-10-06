import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/layout/AppShell";
import { AnalysisProvider } from "@/context/AnalysisContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "GeoIntelligence AI",
  description:
    "AI-powered geopolitical conflict and economic impact intelligence platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <AuthProvider>
            <AnalysisProvider>
              <AppShell>{children}</AppShell>
            </AnalysisProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}