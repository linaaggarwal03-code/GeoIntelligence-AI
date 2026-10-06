"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useAnalysis } from "@/context/AnalysisContext";
import { computeIntelligence } from "@/lib/intelligenceEngine";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  ChevronDown,
  Compass,
  Download,
  Flame,
  Globe2,
  Layers,
  MapPin,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  SlidersHorizontal,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PRESET_PAIRS = [
  { c1: "India", c2: "Pakistan", label: "India ↔ Pakistan" },
  { c1: "United States", c2: "China", label: "US ↔ China" },
  { c1: "Russia", c2: "Ukraine", label: "Russia ↔ Ukraine" },
  { c1: "Israel", c2: "Iran", label: "Israel ↔ Iran" },
];

const HORIZON_OPTIONS = [
  { value: "30", label: "30 Days" },
  { value: "90", label: "90 Days" },
  { value: "180", label: "6 Months" },
  { value: "365", label: "12 Months" },
];

export default function OverviewPage() {
  const { country1, country2, period, focus, setAnalysis } = useAnalysis();

  // Local state initialized with context or sensible defaults
  const [activeC1, setActiveC1] = useState(country1 || "India");
  const [activeC2, setActiveC2] = useState(country2 || "Pakistan");
  const [activePeriod, setActivePeriod] = useState(period || "90");
  const [activeFocus, setActiveFocus] = useState<string[]>(
    focus && focus.length > 0 ? focus : ["conflict", "economy", "energy", "global_impact"]
  );
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [customC1, setCustomC1] = useState(country1 || "India");
  const [customC2, setCustomC2] = useState(country2 || "Pakistan");
  const [isExporting, setIsExporting] = useState(false);

  // Synchronize when context updates
  const effectiveC1 = activeC1 || "India";
  const effectiveC2 = activeC2 || "Pakistan";

  // Compute dynamic intelligence
  const intel = useMemo(() => {
    return computeIntelligence(effectiveC1, effectiveC2, activePeriod, activeFocus);
  }, [effectiveC1, effectiveC2, activePeriod, activeFocus]);

  const handleApplyPreset = (c1: string, c2: string) => {
    setActiveC1(c1);
    setActiveC2(c2);
    setAnalysis(c1, c2, activePeriod, activeFocus);
  };

  const handlePeriodChange = (p: string) => {
    setActivePeriod(p);
    setAnalysis(effectiveC1, effectiveC2, p, activeFocus);
  };

  const toggleFocusDomain = (domain: string) => {
    const updated = activeFocus.includes(domain)
      ? activeFocus.filter((d) => d !== domain)
      : [...activeFocus, domain];
    if (updated.length === 0) return; // Keep at least one
    setActiveFocus(updated);
    setAnalysis(effectiveC1, effectiveC2, activePeriod, updated);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customC1.trim() || !customC2.trim()) return;
    setActiveC1(customC1.trim());
    setActiveC2(customC2.trim());
    setAnalysis(customC1.trim(), customC2.trim(), activePeriod, activeFocus);
    setShowConfigModal(false);
  };

  const handleExportBriefing = () => {
    setIsExporting(true);
    setTimeout(() => {
      window.print();
      setIsExporting(false);
    }, 400);
  };

  // Color helper for scores
  const getScoreColor = (score: number) => {
    if (score >= 75) return "text-red-600 dark:text-red-400";
    if (score >= 55) return "text-amber-600 dark:text-amber-400";
    return "text-emerald-600 dark:text-emerald-400";
  };

  const getScoreBadge = (score: number) => {
    if (score >= 75)
      return "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800";
    if (score >= 55)
      return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800";
    return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800";
  };

  return (
    <div className="min-h-full p-6 lg:p-8">
      <div className="mx-auto max-w-[1550px] space-y-6">

        {/* Top Header & Interactive Pair Selector */}
        <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622] lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-400">
                Live Geopolitical Intelligence Dashboard
              </p>
            </div>

            <div className="mt-1.5 flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {effectiveC1} <span className="text-blue-600 dark:text-blue-400">↔</span> {effectiveC2}
              </h1>

              <button
                type="button"
                onClick={() => setShowConfigModal(!showConfigModal)}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <SlidersHorizontal className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                Change Target
                <ChevronDown className="h-3 w-3 text-slate-400" />
              </button>
            </div>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Multi-domain forecasting: Conflict escalation, macroeconomics, energy flows, and regional systemic risk.
            </p>
          </div>

          {/* Quick Preset Selector & Export Action */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-[#0c1018]">
              {PRESET_PAIRS.map((p) => {
                const isActive =
                  (effectiveC1.toLowerCase().includes(p.c1.toLowerCase()) || p.c1.toLowerCase().includes(effectiveC1.toLowerCase())) &&
                  (effectiveC2.toLowerCase().includes(p.c2.toLowerCase()) || p.c2.toLowerCase().includes(effectiveC2.toLowerCase()));

                return (
                  <button
                    key={p.label}
                    onClick={() => handleApplyPreset(p.c1, p.c2)}
                    className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                      isActive
                        ? "bg-blue-600 text-white shadow-sm"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleExportBriefing}
              disabled={isExporting}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <Download className="h-3.5 w-3.5 text-slate-500" />
              Export Briefing
            </button>
          </div>
        </div>

        {/* Custom Target Switcher Drawer / Inline Box */}
        {showConfigModal && (
          <form
            onSubmit={handleCustomSubmit}
            className="flex flex-col gap-3 rounded-xl border border-blue-200 bg-blue-50/70 p-4 transition dark:border-blue-900/50 dark:bg-blue-950/20 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex flex-1 flex-wrap items-center gap-3">
              <div>
                <label className="block text-[10px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Country 1
                </label>
                <input
                  type="text"
                  value={customC1}
                  onChange={(e) => setCustomC1(e.target.value)}
                  placeholder="e.g. Taiwan"
                  className="mt-1 h-8 rounded-lg border border-slate-300 bg-white px-2.5 text-xs font-medium text-slate-800 outline-none focus:border-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <span className="mt-4 font-bold text-slate-400">↔</span>

              <div>
                <label className="block text-[10px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Country 2
                </label>
                <input
                  type="text"
                  value={customC2}
                  onChange={(e) => setCustomC2(e.target.value)}
                  placeholder="e.g. China"
                  className="mt-1 h-8 rounded-lg border border-slate-300 bg-white px-2.5 text-xs font-medium text-slate-800 outline-none focus:border-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="submit"
                className="rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                Simulate Pair
              </button>
              <button
                type="button"
                onClick={() => setShowConfigModal(false)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Filter Controls Bar: Forecast Horizon & Focus Domains */}
        <div className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622] sm:flex-row sm:items-center sm:justify-between">
          {/* Horizon Selection */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Forecast Window:
            </span>
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900">
              {HORIZON_OPTIONS.map((h) => (
                <button
                  key={h.value}
                  onClick={() => handlePeriodChange(h.value)}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                    activePeriod === h.value
                      ? "bg-white font-semibold text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                  }`}
                >
                  {h.label}
                </button>
              ))}
            </div>
          </div>

          {/* Focus Domains */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Active Domains:
            </span>
            {[
              { id: "conflict", label: "Conflict" },
              { id: "economy", label: "Economy" },
              { id: "energy", label: "Energy" },
              { id: "global_impact", label: "Global Impact" },
            ].map((d) => {
              const selected = activeFocus.includes(d.id);
              return (
                <button
                  key={d.id}
                  onClick={() => toggleFocusDomain(d.id)}
                  className={`rounded-md border px-2.5 py-1 text-xs font-medium transition ${
                    selected
                      ? "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
                      : "border-slate-200 bg-slate-50 text-slate-500 opacity-60 hover:opacity-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
                  }`}
                >
                  {selected ? "✓ " : ""}{d.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Functional Metric Cards Row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Card 1: Escalation Indicator */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Composite Escalation
              </span>
              <div className="rounded-lg bg-blue-50 p-2 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
                <Activity className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold tracking-tight ${getScoreColor(intel.escalationScore)}`}>
                {intel.escalationScore}
              </span>
              <span className="text-xs font-medium text-slate-400">/ 100</span>

              <span
                className={`ml-auto flex items-center text-xs font-semibold ${
                  intel.escalationChange >= 0
                    ? "text-red-500 dark:text-red-400"
                    : "text-emerald-500 dark:text-emerald-400"
                }`}
              >
                {intel.escalationChange >= 0 ? (
                  <TrendingUp className="mr-0.5 h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="mr-0.5 h-3.5 w-3.5" />
                )}
                {intel.escalationChange >= 0 ? `+${intel.escalationChange}%` : `${intel.escalationChange}%`}
              </span>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-slate-500 dark:text-slate-400">Escalation State:</span>
              <span className={`rounded-md border px-2 py-0.5 font-semibold ${getScoreBadge(intel.escalationScore)}`}>
                {intel.conflictStatus}
              </span>
            </div>
          </div>

          {/* Card 2: Conflict & Border Pressure */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Conflict Severity
              </span>
              <div className="rounded-lg bg-red-50 p-2 text-red-600 dark:bg-red-950/40 dark:text-red-400">
                <ShieldAlert className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold tracking-tight ${getScoreColor(intel.conflictScore)}`}>
                {intel.conflictScore}
              </span>
              <span className="text-xs font-medium text-slate-400">/ 100</span>
            </div>

            <div className="mt-3">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-red-500 transition-all duration-500"
                  style={{ width: `${intel.conflictScore}%` }}
                />
              </div>
              <p className="mt-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                Status: <strong className="font-semibold text-slate-700 dark:text-slate-200">{intel.conflictStatus}</strong>
              </p>
            </div>
          </div>

          {/* Card 3: Economic Exposure */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Economy & Market Shock
              </span>
              <div className="rounded-lg bg-amber-50 p-2 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold tracking-tight ${getScoreColor(intel.economyScore)}`}>
                {intel.economyScore}
              </span>
              <span className="text-xs font-medium text-slate-400">/ 100</span>
            </div>

            <div className="mt-3">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-amber-500 transition-all duration-500"
                  style={{ width: `${intel.economyScore}%` }}
                />
              </div>
              <p className="mt-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                Status: <strong className="font-semibold text-slate-700 dark:text-slate-200">{intel.economyStatus}</strong>
              </p>
            </div>
          </div>

          {/* Card 4: Energy & Global Ripple */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Energy & Global Ripple
              </span>
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
                <Globe2 className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold tracking-tight ${getScoreColor(intel.energyScore)}`}>
                {intel.energyScore}
              </span>
              <span className="text-xs font-medium text-slate-400">/ 100</span>
            </div>

            <div className="mt-3">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                  style={{ width: `${intel.energyScore}%` }}
                />
              </div>
              <p className="mt-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                Impact: <strong className="font-semibold text-slate-700 dark:text-slate-200">{intel.globalImpactStatus}</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Main Chart + Radial Assessment Section */}
        <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
          {/* Chart Section */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Escalation Momentum & Forecast Trajectory
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Simulated predictive risk progression across next {activePeriod} days with confidence intervals.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-400" />
                  Risk Index
                </span>
                <span className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-blue-300 dark:bg-blue-800" />
                  Upper Bound
                </span>
              </div>
            </div>

            <div className="mt-6 h-[320px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={intel.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563eb" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#2563eb" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-800" />
                  <XAxis
                    dataKey="horizon"
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={{ stroke: "#cbd5e1" }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={{ stroke: "#cbd5e1" }}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(15, 23, 42, 0.95)",
                      borderRadius: "10px",
                      border: "none",
                      color: "#fff",
                      fontSize: "12px",
                      boxShadow: "0 10px 25px -5px rgba(0,0,0,0.3)",
                    }}
                    labelStyle={{ fontWeight: "bold", color: "#60a5fa" }}
                    formatter={(value: any, name: any) => [
                      `${value}/100`,
                      name === "risk" ? "Risk Level" : name === "upper" ? "Upper Bound" : "Lower Bound",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="#93c5fd"
                    strokeDasharray="4 4"
                    fill="transparent"
                    strokeWidth={1.5}
                  />
                  <Area
                    type="monotone"
                    dataKey="risk"
                    stroke="#2563eb"
                    fill="url(#riskGradient)"
                    strokeWidth={3}
                    dot={{ fill: "#2563eb", strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Radial Assessment & AI Intelligence Summary */}
          <section className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div>
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Intelligence Assessment
                </h2>
                <span className="rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300">
                  {intel.confidence}% CONFIDENCE
                </span>
              </div>

              <div className="my-6 flex items-center justify-center">
                <div className="relative flex h-40 w-40 items-center justify-center rounded-full border-[12px] border-slate-100 dark:border-slate-800">
                  {/* Active arc indicator */}
                  <div
                    className="absolute inset-0 rounded-full border-[12px] border-transparent border-t-blue-600 border-r-blue-600 transition-all duration-700"
                    style={{
                      transform: `rotate(${Math.min(360, intel.escalationScore * 3.6)}deg)`,
                    }}
                  />
                  <div className="text-center">
                    <p className={`text-4xl font-extrabold ${getScoreColor(intel.escalationScore)}`}>
                      {intel.escalationScore}
                    </p>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                      Indicator
                    </p>
                  </div>
                </div>
              </div>

              {/* Dynamic Assessment Paragraph */}
              <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0" />
                  <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    System Synthesis ({effectiveC1} & {effectiveC2})
                  </p>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {intel.summaryText}
                </p>
              </div>
            </div>

            {/* Quick Links / Navigation to Deep Dives */}
            <div className="mt-5 grid grid-cols-2 gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Link
                href="/conflicts"
                className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                Conflict Radar <ArrowRight className="h-3 w-3" />
              </Link>
              <Link
                href="/map"
                className="flex items-center justify-center gap-1.5 rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                World Map View <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
          </section>
        </div>

        {/* Dynamic Key Drivers & Early Warnings Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Key Drivers */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Primary Intelligence Drivers
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Signals heavily weighting the current escalation model.
                </p>
              </div>
              <Compass className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>

            <div className="space-y-3">
              {intel.keyDrivers.map((driver, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5 transition hover:border-slate-200 dark:border-slate-800/80 dark:bg-slate-900/40"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      {driver.title}
                    </span>
                    <span
                      className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                        driver.impact === "high"
                          ? "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300"
                          : "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                      }`}
                    >
                      {driver.impact} impact
                    </span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                    {driver.description}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Early Warning Broadcast */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Early Warning & Threshold Alerts
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Automated surveillance triggers across {effectiveC1} and {effectiveC2}.
                </p>
              </div>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>

            <div className="space-y-3">
              {intel.earlyWarnings.map((warn) => (
                <div
                  key={warn.id}
                  className={`rounded-xl border p-3.5 transition ${
                    warn.type === "critical"
                      ? "border-red-200 bg-red-50/50 dark:border-red-900/40 dark:bg-red-950/20"
                      : "border-slate-100 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          warn.type === "critical"
                            ? "bg-red-500"
                            : warn.type === "warning"
                            ? "bg-amber-500"
                            : "bg-blue-500"
                        }`}
                      />
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {warn.title}
                      </span>
                    </div>
                    <span className="text-[10px] font-medium text-slate-400">
                      {warn.timestamp}
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                    {warn.detail}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400">Want to test market shocks or supply disruptions?</span>
              <Link
                href="/stock"
                className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
              >
                Run Stock Market Stress Test <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </section>
        </div>

      </div>
    </div>
  );
}