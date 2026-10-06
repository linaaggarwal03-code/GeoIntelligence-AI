"use client";

import { useAnalysis } from "@/context/AnalysisContext";
import {
  ArrowDown,
  ArrowUp,
  BarChart3,
  Droplets,
  Globe2,
  Info,
  Ship,
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

const economicForecast = [
  {
    period: "Now",
    impact: 38,
    upper: 44,
    lower: 32,
  },
  {
    period: "30D",
    impact: 43,
    upper: 50,
    lower: 36,
  },
  {
    period: "60D",
    impact: 47,
    upper: 56,
    lower: 39,
  },
  {
    period: "90D",
    impact: 52,
    upper: 62,
    lower: 42,
  },
  {
    period: "120D",
    impact: 50,
    upper: 61,
    lower: 40,
  },
  {
    period: "180D",
    impact: 56,
    upper: 68,
    lower: 44,
  },
];

const impactIndicators = [
  {
    name: "GDP Exposure",
    score: 46,
    level: "Moderate",
    description: "Potential exposure through trade and investment channels.",
  },
  {
    name: "Inflation Pressure",
    score: 59,
    level: "Elevated",
    description: "Energy and supply-chain conditions may increase price pressure.",
  },
  {
    name: "Trade Disruption",
    score: 63,
    level: "Elevated",
    description: "Trade flows may be sensitive to geopolitical developments.",
  },
  {
    name: "Energy Exposure",
    score: 71,
    level: "High",
    description: "Energy prices remain a significant transmission channel.",
  },
];

const horizonData = [
  {
    horizon: "30 Days",
    impact: "Moderate",
    score: 43,
    confidence: "Higher",
  },
  {
    horizon: "90 Days",
    impact: "Elevated",
    score: 52,
    confidence: "Moderate",
  },
  {
    horizon: "180 Days",
    impact: "Elevated",
    score: 56,
    confidence: "Moderate",
  },
];

export default function EconomicImpactPage() {
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
              <BarChart3 className="h-4 w-4 text-blue-600" />

              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600">
                Economic Intelligence
              </p>
            </div>

            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Economic Impact Forecast
            </h1>

            <p className="mt-1.5 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
              Estimate how geopolitical developments may transmit into
              energy, trade, inflation, and broader economic conditions.
            </p>
          </div>

        </div>

        {/* Summary cards */}
        <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {/* Overall impact */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Economic Impact
              </p>

              <BarChart3 className="h-4 w-4 text-blue-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                52
              </span>

              <span className="mb-1 text-[11px] font-medium text-amber-600">
                Elevated
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Overall economic sensitivity
            </p>
          </div>

          {/* Oil */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Oil Sensitivity
              </p>

              <Droplets className="h-4 w-4 text-amber-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                71
              </span>

              <span className="mb-1 flex items-center gap-1 text-[11px] font-medium text-red-500">
                <ArrowUp className="h-3 w-3" />
                High
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Energy-market exposure
            </p>
          </div>

          {/* Trade */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Trade Exposure
              </p>

              <Globe2 className="h-4 w-4 text-blue-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                63
              </span>

              <span className="mb-1 text-[11px] font-medium text-amber-600">
                Elevated
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Supply-chain sensitivity
            </p>
          </div>

          {/* Shipping */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Shipping Risk
              </p>

              <Ship className="h-4 w-4 text-red-500" />
            </div>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-2xl font-semibold text-slate-800">
                57
              </span>

              <span className="mb-1 text-[11px] font-medium text-amber-600">
                Moderate
              </span>
            </div>

            <p className="mt-1 text-[11px] text-slate-500">
              Maritime disruption exposure
            </p>
          </div>
        </div>

        {/* Main forecast */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Economic Impact Trajectory
              </h2>

              <p className="mt-1 text-[11px] text-slate-400">
                Forecasted economic sensitivity with uncertainty range
              </p>
            </div>

            <span className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-[10px] text-slate-500">
              Selected horizon: {period || "90"} days
            </span>
          </div>

          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={economicForecast}
                margin={{
                  top: 10,
                  right: 10,
                  left: -15,
                  bottom: 0,
                }}
              >
                <defs>
                  <linearGradient
                    id="economicGradient"
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
                  dataKey="period"
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
                  dataKey="impact"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  fill="url(#economicGradient)"
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

        {/* Indicators + Oil */}
        <div className="mb-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          {/* Impact indicators */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Economic Impact Channels
                </h2>

                <p className="mt-1 text-[11px] text-slate-400">
                  Main transmission channels identified by the model
                </p>
              </div>

              <TrendingUp className="h-4 w-4 text-blue-500" />
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {impactIndicators.map((indicator) => (
                <div
                  key={indicator.name}
                  className="rounded-xl border border-slate-100 bg-slate-50/60 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold text-slate-700">
                        {indicator.name}
                      </p>

                      <p className="mt-1 text-[10px] leading-4 text-slate-400">
                        {indicator.description}
                      </p>
                    </div>

                    <span className="text-sm font-semibold text-slate-800">
                      {indicator.score}
                    </span>
                  </div>

                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-full rounded-full ${
                        indicator.score >= 70
                          ? "bg-red-500"
                          : indicator.score >= 50
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{
                        width: `${indicator.score}%`,
                      }}
                    />
                  </div>

                  <p className="mt-2 text-[10px] text-slate-400">
                    {indicator.level} exposure
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Oil intelligence */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Oil Market Sensitivity
                </h2>

                <p className="mt-1 text-[11px] text-slate-400">
                  Geopolitical transmission into energy markets
                </p>
              </div>

              <Droplets className="h-4 w-4 text-amber-500" />
            </div>

            <div className="mt-5 rounded-xl border border-amber-100 bg-amber-50/60 p-4">
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-amber-700/70">
                    Sensitivity Indicator
                  </p>

                  <p className="mt-1 text-3xl font-semibold text-slate-800">
                    71
                  </p>
                </div>

                <span className="flex items-center gap-1 rounded-md bg-white px-2 py-1 text-[10px] font-medium text-red-500 shadow-sm">
                  <ArrowUp className="h-3 w-3" />
                  Elevated
                </span>
              </div>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-amber-100">
                <div
                  className="h-full rounded-full bg-amber-500"
                  style={{ width: "71%" }}
                />
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs text-slate-500">
                  Supply disruption sensitivity
                </span>

                <span className="text-xs font-semibold text-slate-700">
                  High
                </span>
              </div>

              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs text-slate-500">
                  Price volatility exposure
                </span>

                <span className="text-xs font-semibold text-slate-700">
                  Elevated
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Energy-import sensitivity
                </span>

                <span className="text-xs font-semibold text-slate-700">
                  Moderate
                </span>
              </div>
            </div>
          </section>
        </div>

        {/* Horizons */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-slate-800">
              Economic Forecast Horizons
            </h2>

            <p className="mt-1 text-[11px] text-slate-400">
              Expected impact across multiple time windows
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[650px]">
              <thead>
                <tr className="border-b border-slate-100 text-left">
                  <th className="px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Horizon
                  </th>

                  <th className="px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Impact
                  </th>

                  <th className="px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Indicator
                  </th>

                  <th className="px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Confidence
                  </th>
                </tr>
              </thead>

              <tbody>
                {horizonData.map((item) => (
                  <tr
                    key={item.horizon}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="px-3 py-4 text-xs font-medium text-slate-700">
                      {item.horizon}
                    </td>

                    <td className="px-3 py-4">
                      <span
                        className={`rounded-md px-2 py-1 text-[10px] font-medium ${
                          item.score >= 65
                            ? "bg-red-50 text-red-600"
                            : item.score >= 50
                            ? "bg-amber-50 text-amber-600"
                            : "bg-emerald-50 text-emerald-600"
                        }`}
                      >
                        {item.impact}
                      </span>
                    </td>

                    <td className="px-3 py-4 text-xs font-semibold text-slate-700">
                      {item.score}/100
                    </td>

                    <td className="px-3 py-4 text-[11px] text-slate-500">
                      {item.confidence}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Shipping risk */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50">
                <Ship className="h-4 w-4 text-red-500" />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Shipping Risk Indicator
                </h2>

                <p className="mt-1 text-[11px] leading-5 text-slate-500">
                  Estimated exposure of maritime trade and logistics
                  channels to geopolitical disruption.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-[10px] uppercase tracking-wider text-slate-400">
                  Current Indicator
                </p>

                <p className="mt-1 text-xl font-semibold text-slate-800">
                  57
                </p>
              </div>

              <span className="rounded-lg bg-amber-50 px-3 py-2 text-[10px] font-medium text-amber-600">
                Moderate
              </span>
            </div>
          </div>
        </section>

        {/* Methodology */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <Info className="h-4 w-4 text-blue-600" />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Economic Intelligence Methodology
              </h2>

              <p className="mt-1 text-[11px] leading-5 text-slate-500">
                Production forecasts will combine historical energy
                prices, geopolitical and conflict indicators, trade
                exposure, macroeconomic variables, and shipping-related
                signals. The model will provide uncertainty ranges rather
                than treating economic outcomes as deterministic.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}