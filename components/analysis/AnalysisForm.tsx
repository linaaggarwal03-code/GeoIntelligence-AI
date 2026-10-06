"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeftRight,
  ArrowRight,
  Check,
  Compass,
  Database,
  Flame,
  Globe2,
  Layers,
  Loader2,
  Radio,
  Satellite,
  Shield,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useAnalysis } from "@/context/AnalysisContext";

const PRESET_PAIRS = [
  { c1: "India", c2: "Pakistan", flag1: "🇮🇳", flag2: "🇵🇰" },
  { c1: "United States", c2: "China", flag1: "🇺🇸", flag2: "🇨🇳" },
  { c1: "Russia", c2: "Ukraine", flag1: "🇷🇺", flag2: "🇺🇦" },
  { c1: "Israel", c2: "Iran", flag1: "🇮🇱", flag2: "🇮🇷" },
];

const PERIOD_OPTIONS = [
  { value: "30", label: "30 Days", desc: "Tactical Horizon", badge: "Short-Term" },
  { value: "90", label: "90 Days", desc: "Quarterly Baseline", badge: "Standard" },
  { value: "180", label: "6 Months", desc: "Mid-Range Horizon", badge: "Extended" },
  { value: "365", label: "12 Months", desc: "Strategic Outlook", badge: "Annual" },
];

const focusAreas = [
  {
    id: "conflict",
    title: "Conflict",
    description: "Kinetic escalations, border mobilization & armed encounters",
    icon: ShieldAlert,
    accent: "text-red-500 dark:text-red-400",
    borderActive: "border-red-400 dark:border-red-500",
    bgActive: "bg-red-50/70 dark:bg-red-950/30",
    dotColor: "bg-red-500",
  },
  {
    id: "economy",
    title: "Economy",
    description: "Trade sanctions, macro supply shocks & currency volatility",
    icon: TrendingUp,
    accent: "text-blue-500 dark:text-blue-400",
    borderActive: "border-blue-400 dark:border-blue-500",
    bgActive: "bg-blue-50/70 dark:bg-blue-950/30",
    dotColor: "bg-blue-500",
  },
  {
    id: "energy",
    title: "Energy",
    description: "Hydrocarbon flows, chokepoint interdiction & pipeline risks",
    icon: Zap,
    accent: "text-amber-500 dark:text-amber-400",
    borderActive: "border-amber-400 dark:border-amber-500",
    bgActive: "bg-amber-50/70 dark:bg-amber-950/30",
    dotColor: "bg-amber-500",
  },
  {
    id: "global_impact",
    title: "Global Impact",
    description: "Multilateral treaty strains, alliance shifts & diplomatic ripple",
    icon: Globe2,
    accent: "text-emerald-500 dark:text-emerald-400",
    borderActive: "border-emerald-400 dark:border-emerald-500",
    bgActive: "bg-emerald-50/70 dark:bg-emerald-950/30",
    dotColor: "bg-emerald-500",
  },
];

export default function AnalysisForm() {
  const router = useRouter();

  // Shared analysis state
  const { setAnalysis } = useAnalysis();

  const [country1, setCountry1] = useState("");
  const [country2, setCountry2] = useState("");
  const [period, setPeriod] = useState("90");

  const [selectedAreas, setSelectedAreas] = useState<string[]>([
    "conflict",
    "economy",
  ]);

  const [isRunning, setIsRunning] = useState(false);
  const [swapRotated, setSwapRotated] = useState(false);

  const toggleArea = (id: string) => {
    setSelectedAreas((current) =>
      current.includes(id)
        ? current.filter((area) => area !== id)
        : [...current, id]
    );
  };

  const swapCountries = () => {
    setSwapRotated(!swapRotated);
    const temp = country1;
    setCountry1(country2);
    setCountry2(temp);
  };

  const applyPreset = (c1: string, c2: string) => {
    setCountry1(c1);
    setCountry2(c2);
  };

  const runAnalysis = async () => {
    if (!country1.trim() || !country2.trim()) {
      alert("Please enter both countries or regions.");
      return;
    }

    if (selectedAreas.length === 0) {
      alert("Please select at least one focus area.");
      return;
    }

    setIsRunning(true);

    // Simulated computation latency
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Save the selected analysis globally
    setAnalysis(
      country1.trim(),
      country2.trim(),
      period,
      selectedAreas
    );

    router.push("/overview");
  };

  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-200/90 bg-white/85 p-6 shadow-2xl backdrop-blur-xl transition-all duration-300 dark:border-white/10 dark:bg-[#0e1424]/90 sm:p-8">
      {/* Decorative Cyber Corner Accents */}
      <div className="pointer-events-none absolute left-0 top-0 h-10 w-10 border-l-2 border-t-2 border-blue-500/40" />
      <div className="pointer-events-none absolute right-0 top-0 h-10 w-10 border-r-2 border-t-2 border-blue-500/40" />
      <div className="pointer-events-none absolute bottom-0 left-0 h-10 w-10 border-b-2 border-l-2 border-blue-500/40" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-10 w-10 border-b-2 border-r-2 border-blue-500/40" />

      {/* Form Header with Live Parameters & Preset Quick-Select */}
      <div className="mb-7 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white">
              Target Bilateral Parameters
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Define target sovereign actors, analytical time horizon, and intelligence domains.
          </p>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">
            PRESETS:
          </span>
          <div className="flex flex-wrap items-center gap-1.5">
            {PRESET_PAIRS.map((p) => {
              const isActive =
                country1.toLowerCase() === p.c1.toLowerCase() &&
                country2.toLowerCase() === p.c2.toLowerCase();

              return (
                <button
                  key={`${p.c1}-${p.c2}`}
                  type="button"
                  onClick={() => applyPreset(p.c1, p.c2)}
                  className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all ${
                    isActive
                      ? "border-blue-500 bg-blue-600 text-white shadow-md shadow-blue-500/20"
                      : "border-slate-200/90 bg-slate-50/80 text-slate-700 hover:border-blue-300 hover:bg-blue-50/60 dark:border-slate-700/80 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-blue-800 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>{p.flag1}</span>
                  <span>{p.c1}</span>
                  <span className="text-slate-400 font-mono">↔</span>
                  <span>{p.flag2}</span>
                  <span>{p.c2}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bilateral Country Inputs with Interactive Swap */}
      <div className="relative grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-end">
        {/* Country 1 */}
        <div className="group">
          <label className="mb-2 flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
              Primary Country / Region 1
            </span>
            <span className="font-mono text-[10px] text-slate-400 uppercase">ACTOR 01</span>
          </label>

          <div className="relative">
            <div className="pointer-events-none absolute left-3.5 top-3.5 text-slate-400">
              <Globe2 className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={country1}
              onChange={(e) => setCountry1(e.target.value)}
              placeholder="e.g. India, United States, Israel"
              className="h-12 w-full rounded-2xl border border-slate-200/90 bg-slate-50/70 pl-10 pr-4 text-sm font-medium text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/15 dark:border-slate-700/80 dark:bg-slate-900/80 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-500 dark:focus:ring-blue-500/20 shadow-inner"
            />
          </div>
        </div>

        {/* Swap Button */}
        <div className="flex justify-center md:pb-1">
          <button
            type="button"
            onClick={swapCountries}
            title="Swap bilateral positions"
            className="group flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200/90 bg-slate-50 text-slate-600 shadow-sm transition-all duration-300 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600 active:scale-95 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-blue-500 dark:hover:bg-slate-700 dark:hover:text-blue-400"
          >
            <ArrowLeftRight
              className={`h-4 w-4 transition-transform duration-300 ${
                swapRotated ? "rotate-180" : "rotate-0"
              }`}
            />
          </button>
        </div>

        {/* Country 2 */}
        <div className="group">
          <label className="mb-2 flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
              Adversary / Region 2
            </span>
            <span className="font-mono text-[10px] text-slate-400 uppercase">ACTOR 02</span>
          </label>

          <div className="relative">
            <div className="pointer-events-none absolute left-3.5 top-3.5 text-slate-400">
              <Compass className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={country2}
              onChange={(e) => setCountry2(e.target.value)}
              placeholder="e.g. Pakistan, China, Iran"
              className="h-12 w-full rounded-2xl border border-slate-200/90 bg-slate-50/70 pl-10 pr-4 text-sm font-medium text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/15 dark:border-slate-700/80 dark:bg-slate-900/80 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-500 dark:focus:ring-blue-500/20 shadow-inner"
            />
          </div>
        </div>
      </div>

      {/* Forecasting Window & Time Horizon Cards */}
      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Forecasting Window & Time Horizon
          </label>
          <span className="font-mono text-[10px] text-blue-600 dark:text-blue-400 font-semibold">
            {period} DAYS SELECTED
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {PERIOD_OPTIONS.map((opt) => {
            const isSelected = period === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setPeriod(opt.value)}
                className={`relative rounded-2xl border p-4 text-left transition-all duration-200 ${
                  isSelected
                    ? "border-blue-500 bg-blue-50/80 shadow-md ring-2 ring-blue-500/30 dark:border-blue-500 dark:bg-blue-950/40"
                    : "border-slate-200/80 bg-slate-50/50 hover:border-slate-300 hover:bg-white dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-slate-700 dark:hover:bg-slate-800/80"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                      isSelected
                        ? "bg-blue-600 text-white"
                        : "bg-slate-200/80 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                    }`}
                  >
                    {opt.badge}
                  </span>
                  <span className={`h-2 w-2 rounded-full ${isSelected ? "bg-blue-500 animate-pulse" : "bg-transparent"}`} />
                </div>

                <p className={`mt-2.5 text-sm font-black ${isSelected ? "text-blue-600 dark:text-blue-400" : "text-slate-900 dark:text-white"}`}>
                  {opt.label}
                </p>

                <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                  {opt.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Focus Areas: Interactive Domain Vector Cards */}
      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Active Intelligence Focus Domains
            </label>
            <p className="mt-0.5 text-[11px] text-slate-400 dark:text-slate-500">
              Select one or more analytical vectors to calibrate the forecasting engine.
            </p>
          </div>
          <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-bold text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
            {selectedAreas.length} / 4 Vectors Active
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {focusAreas.map((area) => {
            const selected = selectedAreas.includes(area.id);
            const Icon = area.icon;

            return (
              <button
                key={area.id}
                type="button"
                onClick={() => toggleArea(area.id)}
                className={`group relative rounded-2xl border p-4 text-left transition-all duration-200 ${
                  selected
                    ? `border-blue-500 bg-blue-50/80 shadow-md ring-2 ring-blue-500/20 dark:border-blue-500 dark:bg-blue-950/40`
                    : "border-slate-200/90 bg-slate-50/40 hover:border-slate-300 hover:bg-white dark:border-slate-800 dark:bg-slate-900/40 dark:hover:border-slate-700 dark:hover:bg-slate-800/60"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-xl shadow-sm ${
                        selected
                          ? "bg-white dark:bg-slate-800"
                          : "bg-slate-100 dark:bg-slate-800"
                      }`}
                    >
                      <Icon className={`h-4 w-4 ${area.accent}`} />
                    </div>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      {area.title}
                    </span>
                  </div>

                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full border transition-all ${
                      selected
                        ? "border-blue-600 bg-blue-600 text-white shadow-sm"
                        : "border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800"
                    }`}
                  >
                    {selected && <Check className="h-3 w-3 stroke-[3]" />}
                  </span>
                </div>

                <p className="mt-2.5 text-[11px] leading-relaxed text-slate-600 dark:text-slate-400 font-medium">
                  {area.description}
                </p>

                {/* Subtle active footer status */}
                <div className="mt-3 flex items-center gap-1.5 pt-2 border-t border-slate-100 dark:border-white/5 text-[10px]">
                  <span className={`h-1.5 w-1.5 rounded-full ${selected ? area.dotColor : "bg-slate-300 dark:bg-slate-600"}`} />
                  <span className={selected ? "font-semibold text-slate-700 dark:text-slate-300" : "text-slate-400"}>
                    {selected ? "Active in Model" : "Standby"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Telemetry Info & High-Impact Launch Button */}
      <div className="mt-8 flex flex-col gap-4 border-t border-slate-100 pt-6 dark:border-white/5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5 text-blue-500" />
            <span className="font-medium">ACLED · UCDP · World Bank</span>
          </div>
          <span className="text-slate-300 dark:text-slate-700">•</span>
          <div className="flex items-center gap-1.5">
            <Satellite className="h-3.5 w-3.5 text-emerald-500" />
            <span className="font-medium">Live Satcom AIS Telemetry</span>
          </div>
        </div>

        <button
          type="button"
          onClick={runAnalysis}
          disabled={isRunning}
          className="group relative flex items-center justify-center gap-3 overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 px-7 py-3.5 text-xs font-black uppercase tracking-wider text-white shadow-xl shadow-blue-500/25 transition-all duration-300 hover:from-blue-700 hover:via-indigo-700 hover:to-blue-800 hover:shadow-blue-500/40 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isRunning ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Simulating Intelligence Vectors...</span>
            </>
          ) : (
            <>
              <span>Initialize Forecasting Engine</span>
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
            </>
          )}
        </button>
      </div>
    </section>
  );
}