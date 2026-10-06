"use client";

import { useAnalysis } from "@/context/AnalysisContext";
import {
  Activity,
  ArrowDown,
  ArrowUp,
  CalendarDays,
  Info,
  TrendingUp,
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

const forecastData = [
  { month: "Now", risk: 54, upper: 60, lower: 48 },
  { month: "30D", risk: 58, upper: 66, lower: 50 },
  { month: "60D", risk: 61, upper: 70, lower: 52 },
  { month: "90D", risk: 64, upper: 74, lower: 54 },
  { month: "120D", risk: 62, upper: 73, lower: 51 },
  { month: "180D", risk: 67, upper: 79, lower: 55 },
];

const signals = [
  {
    name: "Conflict Activity",
    value: 72,
    change: "+8%",
    direction: "up",
    description: "Recent event activity remains elevated.",
  },
  {
    name: "Political Tension",
    value: 64,
    change: "+5%",
    direction: "up",
    description: "Diplomatic and political signals show pressure.",
  },
  {
    name: "Economic Exposure",
    value: 58,
    change: "+3%",
    direction: "up",
    description: "Trade and macroeconomic sensitivity is moderate.",
  },
  {
    name: "Energy Sensitivity",
    value: 61,
    change: "-2%",
    direction: "down",
    description: "Energy-market exposure has slightly eased.",
  },
];

const horizons = [
  {
    period: "30 Days",
    score: 58,
    level: "Moderate",
    confidence: "Higher",
  },
  {
    period: "90 Days",
    score: 64,
    level: "Elevated",
    confidence: "Moderate",
  },
  {
    period: "180 Days",
    score: 67,
    level: "Elevated",
    confidence: "Moderate",
  },
];

export default function ForecastPage() {
  const { country1, country2, period } = useAnalysis();

  const displayCountry1 = country1 || "Country 1";
  const displayCountry2 = country2 || "Country 2";

  return (
    <div className="min-h-full p-7">
      <div className="mx-auto max-w-[1550px]">
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />

              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600">
                Predictive Intelligence
              </p>
            </div>

            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Escalation Forecast
            </h1>

            <p className="mt-1.5 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
              Explore how geopolitical pressure may evolve across multiple
              forecast horizons using historical and current intelligence
              signals.
            </p>
          </div>

        </div>

        {/* Summary cards */}
        <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Current Indicator
              </p>

              <Activity className="h-4 w-4 text-blue-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                54
              </span>

              <span className="mb-1 text-[11px] font-medium text-amber-600">
                Moderate
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Current escalation momentum
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                30-Day Outlook
              </p>

              <CalendarDays className="h-4 w-4 text-blue-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                58
              </span>

              <span className="mb-1 flex items-center gap-1 text-[11px] font-medium text-red-500">
                <ArrowUp className="h-3 w-3" />
                +4
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Expected near-term pressure
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                90-Day Outlook
              </p>

              <TrendingUp className="h-4 w-4 text-amber-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                64
              </span>

              <span className="mb-1 text-[11px] font-medium text-amber-600">
                Elevated
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Medium-term escalation indicator
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Model Confidence
              </p>

              <Info className="h-4 w-4 text-slate-400" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                76%
              </span>

              <span className="mb-1 text-[11px] font-medium text-emerald-600">
                Good
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Forecast reliability estimate
            </p>
          </div>
        </div>

        {/* Chart */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Escalation Indicator Forecast
              </h2>

              <p className="mt-1 text-[11px] text-slate-400">
                Model-estimated geopolitical pressure with uncertainty range
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-[10px] text-slate-500">
              Selected horizon: {period || "90"} days
            </div>
          </div>

          <div className="h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={forecastData}
                margin={{
                  top: 10,
                  right: 10,
                  left: -15,
                  bottom: 0,
                }}
              >
                <defs>
                  <linearGradient
                    id="forecastGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#2563eb"
                      stopOpacity={0.2}
                    />

                    <stop
                      offset="100%"
                      stopColor="#2563eb"
                      stopOpacity={0.02}
                    />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  stroke="#e2e8f0"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="month"
                  tick={{
                    fontSize: 11,
                    fill: "#64748b",
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <YAxis
                  domain={[0, 100]}
                  tick={{
                    fontSize: 11,
                    fill: "#64748b",
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <Tooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid #e2e8f0",
                    boxShadow:
                      "0 4px 16px rgba(15,23,42,0.08)",
                    fontSize: 12,
                  }}
                />

                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="transparent"
                  fill="#e2e8f0"
                  fillOpacity={0.55}
                />

                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="transparent"
                  fill="#ffffff"
                  fillOpacity={1}
                />

                <Area
                  type="monotone"
                  dataKey="risk"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  fill="url(#forecastGradient)"
                  dot={{
                    r: 3,
                    fill: "#2563eb",
                    strokeWidth: 0,
                  }}
                  activeDot={{
                    r: 5,
                    fill: "#2563eb",
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Lower */}
        <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          {/* Horizons */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Forecast Horizons
                </h2>

                <p className="mt-1 text-[11px] text-slate-400">
                  Indicator across different prediction windows
                </p>
              </div>

              <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] text-slate-500">
                MULTI-HORIZON
              </span>
            </div>

            <div className="mt-5 overflow-hidden rounded-xl border border-slate-100">
              <div className="grid grid-cols-4 border-b border-slate-100 bg-slate-50 px-4 py-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                <span>Horizon</span>
                <span>Indicator</span>
                <span>Level</span>
                <span>Confidence</span>
              </div>

              {horizons.map((item) => (
                <div
                  key={item.period}
                  className="grid grid-cols-4 items-center border-b border-slate-100 px-4 py-4 last:border-0"
                >
                  <span className="text-xs font-medium text-slate-700">
                    {item.period}
                  </span>

                  <span className="text-xs font-semibold text-slate-800">
                    {item.score}/100
                  </span>

                  <span
                    className={`w-fit rounded-md px-2 py-1 text-[10px] font-medium ${
                      item.score >= 65
                        ? "bg-red-50 text-red-600"
                        : item.score >= 50
                        ? "bg-amber-50 text-amber-600"
                        : "bg-emerald-50 text-emerald-600"
                    }`}
                  >
                    {item.level}
                  </span>

                  <span className="text-[11px] text-slate-500">
                    {item.confidence}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Drivers */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Forecast Drivers
              </h2>

              <p className="mt-1 text-[11px] text-slate-400">
                Signals currently influencing the forecast
              </p>
            </div>

            <div className="mt-5 space-y-4">
              {signals.map((signal) => (
                <div
                  key={signal.name}
                  className="rounded-xl border border-slate-100 bg-slate-50/60 p-3.5"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-slate-700">
                        {signal.name}
                      </p>

                      <p className="mt-1 text-[10px] leading-4 text-slate-400">
                        {signal.description}
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-800">
                        {signal.value}
                      </p>

                      <p
                        className={`mt-0.5 flex items-center justify-end gap-0.5 text-[10px] font-medium ${
                          signal.direction === "up"
                            ? "text-red-500"
                            : "text-emerald-600"
                        }`}
                      >
                        {signal.direction === "up" ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : (
                          <ArrowDown className="h-3 w-3" />
                        )}

                        {signal.change}
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{
                        width: `${signal.value}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Methodology */}
        <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <Info className="h-4 w-4 text-blue-600" />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Forecast Methodology
              </h2>

              <p className="mt-1 text-[11px] leading-5 text-slate-500">
                The production model will combine historical conflict
                activity, geopolitical signals, economic indicators,
                energy-market conditions, and structured news intelligence.
                Forecasts should be evaluated using time-based validation
                and reported with uncertainty rather than presented as
                deterministic predictions.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}