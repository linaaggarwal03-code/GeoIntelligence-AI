import AnalysisForm from "@/components/analysis/AnalysisForm";
import { Activity, Globe2, Radio, Shield, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="relative min-h-[calc(100vh-76px)] overflow-hidden p-6 lg:p-8">
      {/* Tactical Geospatial Background Layer */}
      <div className="pointer-events-none absolute inset-0 z-0 select-none overflow-hidden">
        {/* High-Resolution Tactical World Map Background */}
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-35 dark:opacity-25 transition-opacity duration-700"
          style={{ backgroundImage: `url('/images/tactical_map_bg.jpg')` }}
        />

        {/* Ambient Gradient Overlays for High-Contrast Readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#edf2f6]/85 via-[#edf2f6]/75 to-[#edf2f6] dark:from-[#0a0d14]/85 dark:via-[#0a0d14]/85 dark:to-[#0a0d14]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-600/15 via-transparent to-transparent" />
      </div>

      {/* Main Content Layer */}
      <div className="relative z-10 mx-auto max-w-[1500px] space-y-6">

        {/* Hero Header Card */}
        <div className="flex flex-col gap-4 rounded-3xl border border-slate-200/80 bg-white/85 p-6 shadow-xl backdrop-blur-xl transition-all duration-300 dark:border-white/10 dark:bg-[#0e1424]/85 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-blue-500 animate-ping" />
              <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                Geopolitical Intelligence Platform
              </p>
            </div>

            <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-900 dark:text-white sm:text-3xl">
              Start a New Analysis
            </h1>

            <p className="mt-1.5 max-w-2xl text-xs leading-relaxed text-slate-600 dark:text-slate-300">
              Configure sovereign actors, forecasting horizons, and multi-domain intelligence vectors to activate predictive geopolitical modeling.
            </p>
          </div>

          {/* Real-Time Live Status Telemetry Pill */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-2xl border border-slate-200/90 bg-slate-50/90 px-4 py-2.5 text-xs font-bold text-slate-700 shadow-sm backdrop-blur-md dark:border-slate-700/80 dark:bg-slate-900/80 dark:text-slate-200">
              <Activity className="h-4 w-4 text-emerald-500 animate-pulse" />
              <span>Telemetry Operational</span>
              <span className="h-1.5 w-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
              <span className="font-mono text-[10px] text-blue-600 dark:text-blue-400">LIVE FEED</span>
            </div>
          </div>
        </div>

        {/* Operational Capability Indicators Bar */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/70 p-3.5 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-[#111728]/70">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
              <Globe2 className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Coverage</p>
              <p className="text-xs font-bold text-slate-800 dark:text-white">194 Sovereign Nations</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/70 p-3.5 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-[#111728]/70">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/10 text-red-600 dark:bg-red-500/20 dark:text-red-400">
              <Shield className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Signals</p>
              <p className="text-xs font-bold text-slate-800 dark:text-white">ACLED & UCDP Feeds</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/70 p-3.5 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-[#111728]/70">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400">
              <Radio className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Satcom Links</p>
              <p className="text-xs font-bold text-slate-800 dark:text-white">Maritime AIS Active</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/70 p-3.5 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-[#111728]/70">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Precision</p>
              <p className="text-xs font-bold text-slate-800 dark:text-white">Multi-Domain AI Engine</p>
            </div>
          </div>
        </div>

        {/* Analysis Form Component */}
        <AnalysisForm />

      </div>
    </div>
  );
}