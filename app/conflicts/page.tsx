"use client";

import { useAnalysis } from "@/context/AnalysisContext";
import { computeIntelligence } from "@/lib/intelligenceEngine";
import { useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Flame,
  Radio,
  ShieldAlert,
  TrendingUp,
  Zap,
} from "lucide-react";

export default function ConflictsPage() {
  const { country1, country2, period, focus } = useAnalysis();

  const displayCountry1 = country1 || "India";
  const displayCountry2 = country2 || "Pakistan";

  // Compute dynamic data based on active pair
  const intel = useMemo(() => {
    return computeIntelligence(displayCountry1, displayCountry2, period || "90", focus);
  }, [displayCountry1, displayCountry2, period, focus]);

  const signals = [
    {
      name: "Frontline Military Posture",
      score: intel.conflictScore,
      status: intel.conflictStatus,
    },
    {
      name: "Political / Diplomatic Strain",
      score: Math.min(95, intel.conflictScore - 6),
      status: intel.conflictScore > 75 ? "Elevated" : "Moderate",
    },
    {
      name: "Border Security Pressure",
      score: Math.min(95, intel.conflictScore - 12),
      status: "Moderate",
    },
    {
      name: "Asymmetric / Cyber Activity",
      score: Math.min(95, intel.conflictScore - 18),
      status: "Monitored",
    },
  ];

  return (
    <div className="min-h-full p-6 lg:p-8">
      <div className="mx-auto max-w-[1550px] space-y-6">

        {/* Header */}
        <div className="flex flex-col gap-4 rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622] lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-400">
                Conflict Intelligence Radar
              </p>
            </div>

            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Kinetic Escalation & Border Watch
            </h1>

            <p className="mt-1 max-w-2xl text-xs text-slate-500 dark:text-slate-400">
              Live monitoring of conflict activity, kinetic signals, and early warning threshold triggers for the selected pair.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Active Theater
            </p>

            <p className="mt-0.5 text-xs font-bold text-slate-800 dark:text-white">
              {displayCountry1} ↔ {displayCountry2}
            </p>
          </div>
        </div>

        {/* Summary KPI Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Escalation Momentum
              </p>
              <Activity className="h-4 w-4 text-blue-500" />
            </div>

            <p className="mt-2 text-3xl font-extrabold text-slate-800 dark:text-white">
              {intel.escalationScore}
            </p>

            <p className="mt-1 text-[11px] font-semibold text-amber-500">
              {intel.conflictStatus} Phase
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Conflict Severity
              </p>
              <ShieldAlert className="h-4 w-4 text-red-500" />
            </div>

            <p className="mt-2 text-3xl font-extrabold text-red-500">
              {intel.conflictScore}
            </p>

            <p className="mt-1 text-[11px] font-medium text-slate-500 dark:text-slate-400">
              Relative to baseline index
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Surveillance Signals
              </p>
              <Radio className="h-4 w-4 text-amber-500" />
            </div>

            <p className="mt-2 text-3xl font-extrabold text-slate-800 dark:text-white">
              {intel.earlyWarnings.length}
            </p>

            <p className="mt-1 text-[11px] text-amber-500 font-semibold">
              Live threshold triggers
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Spillover Sensitivity
              </p>
              <Flame className="h-4 w-4 text-emerald-500" />
            </div>

            <p className="mt-2 text-3xl font-extrabold text-slate-800 dark:text-white">
              {intel.globalImpactScore}
            </p>

            <p className="mt-1 text-[11px] font-medium text-slate-500 dark:text-slate-400">
              {intel.globalImpactStatus}
            </p>
          </div>
        </div>

        {/* Assessment & Signal Breakdown */}
        <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <h2 className="text-sm font-bold text-slate-800 dark:text-white">
                Escalation Assessment
              </h2>
            </div>

            <div className="mt-6 flex flex-col items-center gap-5 sm:flex-row">
              <div className="relative flex h-28 w-28 shrink-0 items-center justify-center rounded-full border-[10px] border-slate-100 dark:border-slate-800">
                <div
                  className="absolute inset-0 rounded-full border-[10px] border-transparent border-t-red-500 border-r-amber-500"
                  style={{ transform: `rotate(${intel.conflictScore * 2.8}deg)` }}
                />
                <div className="text-center">
                  <p className="text-2xl font-extrabold text-slate-800 dark:text-white">
                    {intel.conflictScore}
                  </p>
                  <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">
                    Indicator
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-bold text-amber-600 dark:text-amber-400">
                  {intel.conflictStatus} Conflict Sensitivity
                </p>

                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  Real-time algorithmic fusion across bilateral telemetry indicates heightened deterrence requirements across {displayCountry1} and {displayCountry2}.
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-800 dark:text-white">
                  Signal Breakdown
                </h2>
                <p className="mt-0.5 text-xs text-slate-400">
                  Model-relevant conflict indicators
                </p>
              </div>
              <Activity className="h-4 w-4 text-slate-400" />
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {signals.map((signal) => (
                <div
                  key={signal.name}
                  className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-900/50"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {signal.name}
                    </span>
                    <span className="text-xs font-bold font-mono text-slate-800 dark:text-white">
                      {signal.score}
                    </span>
                  </div>

                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        signal.score >= 70
                          ? "bg-red-500"
                          : signal.score >= 50
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${signal.score}%` }}
                    />
                  </div>

                  <p className="mt-2 text-[10px] font-medium text-slate-400">
                    {signal.status}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Early Warnings Grid */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition dark:border-slate-800 dark:bg-[#111622]">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <h2 className="text-sm font-bold text-slate-800 dark:text-white">
              Tactical Early Warning Bulletins
            </h2>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {intel.earlyWarnings.map((w) => (
              <div
                key={w.id}
                className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 transition hover:shadow-sm dark:border-slate-800 dark:bg-slate-900/40"
              >
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-slate-800 dark:text-slate-200">{w.title}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{w.timestamp}</span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {w.detail}
                </p>
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
}