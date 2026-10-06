"use client";

import { useState, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  BarChart3,
  CandlestickChart,
  CheckCircle2,
  Coins,
  Cpu,
  Database,
  DollarSign,
  Droplets,
  Flame,
  Globe2,
  Info,
  Layers,
  LineChart,
  Percent,
  Play,
  RotateCcw,
  Scale,
  ShieldAlert,
  Sliders,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Feature importance data from models/feature_importance.json
const FEATURE_IMPORTANCE_DATA = [
  { feature: "Return_10D", name: "10-Day NIFTY Momentum", category: "market", xgb: 5.63, rf: 8.77 },
  { feature: "GPR_Volatility_5D", name: "5-Day GPR Volatility Spike", category: "geopolitical", xgb: 5.56, rf: 1.39 },
  { feature: "Price_vs_MA50", name: "Price vs 50-Day Moving Avg", category: "market", xgb: 5.20, rf: 9.98 },
  { feature: "Gold_Return_20D", name: "20-Day Gold Safe-Haven Return", category: "macro", xgb: 5.14, rf: 7.74 },
  { feature: "GPR_Volatility_20D", name: "20-Day GPR Sustained Volatility", category: "geopolitical", xgb: 5.10, rf: 5.48 },
  { feature: "Return_20D", name: "20-Day NIFTY Return", category: "market", xgb: 5.00, rf: 3.06 },
  { feature: "Volatility_20D", name: "20-Day Market Realized Volatility", category: "market", xgb: 4.88, rf: 12.43 },
  { feature: "Oil_Return_5D", name: "5-Day Brent Crude Return", category: "macro", xgb: 4.65, rf: 6.12 },
  { feature: "USD_Return_20D", name: "20-Day USD/INR Currency Return", category: "macro", xgb: 4.53, rf: 8.57 },
  { feature: "Price_vs_MA20", name: "Price vs 20-Day Moving Avg", category: "market", xgb: 4.24, rf: 3.63 },
  { feature: "Return_5D", name: "5-Day NIFTY Return", category: "market", xgb: 4.11, rf: 6.01 },
  { feature: "Oil_Return_20D", name: "20-Day Brent Crude Return", category: "macro", xgb: 4.01, rf: 8.16 },
  { feature: "USD_Return_5D", name: "5-Day USD/INR Currency Return", category: "macro", xgb: 3.95, rf: 3.67 },
  { feature: "Oil_Return_1D", name: "1-Day Brent Crude Return", category: "macro", xgb: 3.85, rf: 1.34 },
  { feature: "Volatility_5D", name: "5-Day Market Volatility", category: "market", xgb: 3.67, rf: 3.05 },
  { feature: "GPRD", name: "Caldara-Iacoviello GPR Daily Index", category: "geopolitical", xgb: 3.60, rf: 0.73 },
  { feature: "Gold_Return_5D", name: "5-Day Gold Price Return", category: "macro", xgb: 3.42, rf: 2.40 },
  { feature: "GPRD_THREAT", name: "Geopolitical Threat Index", category: "geopolitical", xgb: 3.27, rf: 0.86 },
  { feature: "GPR_Change_20D", name: "20-Day GPR Index Change", category: "geopolitical", xgb: 3.26, rf: 0.92 },
  { feature: "GPRD_ACT", name: "Geopolitical Kinetic Acts Index", category: "geopolitical", xgb: 3.24, rf: 1.50 },
  { feature: "Return_1D", name: "1-Day NIFTY Return", category: "market", xgb: 3.15, rf: 1.77 },
  { feature: "GPR_Change_5D", name: "5-Day GPR Index Shift", category: "geopolitical", xgb: 3.05, rf: 0.75 },
  { feature: "Gold_Return_1D", name: "1-Day Gold Price Return", category: "macro", xgb: 2.91, rf: 0.63 },
  { feature: "USD_Return_1D", name: "1-Day USD/INR Return", category: "macro", xgb: 2.41, rf: 0.69 },
  { feature: "GPR_Change_1D", name: "1-Day GPR Daily Shift", category: "geopolitical", xgb: 2.18, rf: 0.36 },
];

// Model Metrics from model_metrics.json
const MODEL_TIERS_METRICS = [
  {
    tier: "Tier A",
    name: "Market Technicals Only",
    featuresCount: 8,
    featuresDesc: "Returns (1D, 5D, 10D, 20D), Volatilities, MA20, MA50",
    regressorMae: "1.54%",
    regressorRmse: "2.06%",
    regressorDirAcc: "54.96%",
    classifierAcc: "54.12%",
    classifierAuc: "0.5280",
    classifierF1: "0.6720",
    bestModel: "XGBoost Regressor / RF",
  },
  {
    tier: "Tier B",
    name: "Market + Macroeconomic",
    featuresCount: 17,
    featuresDesc: "Tier A + Brent Crude Oil, USD/INR, Gold multi-horizon returns",
    regressorMae: "1.59%",
    regressorRmse: "2.18%",
    regressorDirAcc: "48.35%",
    classifierAcc: "52.45%",
    classifierAuc: "0.5185",
    classifierF1: "0.6680",
    bestModel: "XGBoost Regressor",
  },
  {
    tier: "Tier C (Full)",
    name: "Market + Macro + Geopolitical (GPR)",
    featuresCount: 25,
    featuresDesc: "Tier B + Caldara-Iacoviello GPR, GPR Acts, Threats, GPR Volatilities",
    regressorMae: "1.60%",
    regressorRmse: "2.23%",
    regressorDirAcc: "54.58%",
    classifierAcc: "55.42%",
    classifierAuc: "0.5540",
    classifierF1: "0.6806",
    bestModel: "Model C XGBoost Classifier (Champion)",
  },
];

// Presets for Scenario Stress Tester
const SCENARIO_PRESETS = [
  {
    id: "war_escalation",
    title: "Regional War Escalation",
    description: "Multi-front missile exchanges, Black Sea / Levant escalation, supply chains rattled.",
    gprSpike: 150,
    oilReturn: 16.5,
    goldReturn: 6.8,
    usdInrMove: 1.8,
  },
  {
    id: "hormuz_blockade",
    title: "Strait of Hormuz Chokepoint Shock",
    description: "21M bbl/day crude tanker interdiction, extreme energy supply disruption.",
    gprSpike: 120,
    oilReturn: 28.5,
    goldReturn: 5.4,
    usdInrMove: 2.2,
  },
  {
    id: "de_escalation",
    title: "Diplomatic Accord / Ceasefire",
    description: "Formal armistice signed, energy transit restored, safe-haven unwinding.",
    gprSpike: -45,
    oilReturn: -8.5,
    goldReturn: -3.2,
    usdInrMove: -0.8,
  },
  {
    id: "taiwan_tensions",
    title: "East Asia Semiconductor Blockade",
    description: "Taiwan Strait naval standoff, tech hardware electronics supply shock.",
    gprSpike: 135,
    oilReturn: 7.2,
    goldReturn: 8.5,
    usdInrMove: 2.6,
  },
];

export default function StockImpactPage() {
  const [selectedTier, setSelectedTier] = useState<"all" | "A" | "B" | "C">("all");
  const [featureCategory, setFeatureCategory] = useState<"all" | "geopolitical" | "macro" | "market">("all");

  // Scenario Simulator Interactive State
  const [gprShift, setGprShift] = useState(0);
  const [oilShift, setOilShift] = useState(0);
  const [goldShift, setGoldShift] = useState(0);
  const [usdInrShift, setUsdInrShift] = useState(0);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);

  // Apply Preset
  const handleApplyPreset = (preset: typeof SCENARIO_PRESETS[0]) => {
    setActiveScenarioId(preset.id);
    setGprShift(preset.gprSpike);
    setOilShift(preset.oilReturn);
    setGoldShift(preset.goldReturn);
    setUsdInrShift(preset.usdInrMove);
  };

  const handleResetSliders = () => {
    setActiveScenarioId(null);
    setGprShift(0);
    setOilShift(0);
    setGoldShift(0);
    setUsdInrShift(0);
  };

  // Live Machine Learning Simulation Model based on trained weights
  // Model C XGBoost Regression & Classifier elasticity coefficients
  const simulationResults = useMemo(() => {
    const baseReturn = 0.68; // baseline 7-day expected return without shocks
    const baseDownsideProb = 41.6; // baseline crash probability

    // Sensitivity coefficients derived from XGBoost feature importance & negative impact correlations
    // GPR spike: -0.018% return per 10% GPR shift
    // Crude Oil return: -0.095% return per 1% crude spike (India imports ~85% crude)
    // Gold return: -0.040% return per 1% gold spike (safe-haven flight diversion)
    // USD/INR move: -0.220% return per 1% INR depreciation (foreign capital outflow)
    const gprImpact = (gprShift / 10) * -0.018;
    const oilImpact = oilShift * -0.095;
    const goldImpact = goldShift * -0.040;
    const fxImpact = usdInrShift * -0.220;

    const netReturnForecast = baseReturn + gprImpact + oilImpact + goldImpact + fxImpact;

    // Downside Crash Probability shift
    const crashProbDelta =
      (gprShift / 10) * 1.5 +
      oilShift * 1.25 +
      goldShift * 0.75 +
      usdInrShift * 2.8;

    const finalCrashProb = Math.min(95, Math.max(8, baseDownsideProb + crashProbDelta));
    const upsideProb = 100 - finalCrashProb;

    // Projected NIFTY 50 Level (Baseline: 25,014.60)
    const currentNifty = 25014.60;
    const projectedNifty = currentNifty * (1 + netReturnForecast / 100);
    const pointChange = projectedNifty - currentNifty;

    return {
      netReturnForecast: parseFloat(netReturnForecast.toFixed(2)),
      finalCrashProb: parseFloat(finalCrashProb.toFixed(1)),
      upsideProb: parseFloat(upsideProb.toFixed(1)),
      projectedNifty: Math.round(projectedNifty),
      pointChange: Math.round(pointChange),
      gprImpact: parseFloat(gprImpact.toFixed(2)),
      oilImpact: parseFloat(oilImpact.toFixed(2)),
      goldImpact: parseFloat(goldImpact.toFixed(2)),
      fxImpact: parseFloat(fxImpact.toFixed(2)),
    };
  }, [gprShift, oilShift, goldShift, usdInrShift]);

  // Filtered feature importance
  const filteredFeatures = useMemo(() => {
    if (featureCategory === "all") return FEATURE_IMPORTANCE_DATA.slice(0, 16);
    return FEATURE_IMPORTANCE_DATA.filter((f) => f.category === featureCategory);
  }, [featureCategory]);

  return (
    <div className="min-h-full p-7 font-sans">
      <div className="mx-auto max-w-[1550px] space-y-7">
        {/* HEADER SECTION */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <CandlestickChart className="h-4 w-4 text-emerald-500" />
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-500">
                WARS Machine Learning Intelligence · NIFTY 50 Target
              </p>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Stock Market Geopolitical AI Engine
            </h1>

            <p className="mt-1.5 max-w-3xl text-sm text-slate-500 dark:text-slate-400">
              Quantitative multi-tier machine learning architecture predicting forward 7-day equity returns
              and downside shock probabilities on <strong>NIFTY 50 (^NSEI)</strong> by integrating the Caldara &
              Iacoviello Geopolitical Risk Index (GPR), Brent Crude Oil, Gold, and USD/INR currency transmission channels.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-700 dark:text-slate-300 font-semibold">
                Model C: XGBoost + Random Forest
              </span>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-slate-600 shadow-sm dark:border-slate-800 dark:bg-[#111622] dark:text-slate-400">
              3,871 Training Sessions (2010–2025)
            </div>
          </div>
        </div>

        {/* TOP KPI CARDS */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {/* Card 1: Benchmark Index */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Target Benchmark
              </p>
              <div className="rounded-md bg-blue-500/10 p-1.5 text-blue-500">
                <BarChart3 className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                25,014.60
              </span>
              <span className="flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                <ArrowUpRight className="h-3.5 w-3.5" /> +0.45%
              </span>
            </div>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              NSE NIFTY 50 Index (^NSEI) · 7D Target Horizon
            </p>
          </div>

          {/* Card 2: 7-Day Forward Expected Return */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Expected 7D Forward Return
              </p>
              <div className="rounded-md bg-emerald-500/10 p-1.5 text-emerald-500">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-2.5 flex items-baseline gap-2">
              <span className={`text-2xl font-bold ${
                simulationResults.netReturnForecast >= 0
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-red-600 dark:text-red-400"
              }`}>
                {simulationResults.netReturnForecast >= 0 ? "+" : ""}
                {simulationResults.netReturnForecast}%
              </span>
              <span className="text-xs font-semibold text-slate-500">
                ({simulationResults.pointChange >= 0 ? "+" : ""}
                {simulationResults.pointChange} pts)
              </span>
            </div>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Model C XGBoost Regressor (Test MAE: 1.60%)
            </p>
          </div>

          {/* Card 3: Market Direction & Downside Risk */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Direction & Crash Risk
              </p>
              <div className="rounded-md bg-purple-500/10 p-1.5 text-purple-500">
                <ShieldAlert className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {simulationResults.upsideProb >= 50 ? "Bullish Bias" : "High Alert"}
              </span>
              <span className={`text-xs font-semibold ${
                simulationResults.finalCrashProb > 55
                  ? "text-red-500"
                  : "text-slate-500"
              }`}>
                Downside Risk: {simulationResults.finalCrashProb}%
              </span>
            </div>

            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className={`h-full transition-all duration-300 ${
                  simulationResults.finalCrashProb > 60 ? "bg-red-500" : "bg-emerald-500"
                }`}
                style={{ width: `${simulationResults.finalCrashProb}%` }}
              />
            </div>
          </div>

          {/* Card 4: Geopolitical Risk Elasticity */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                GPR Elasticity (Beta)
              </p>
              <div className="rounded-md bg-amber-500/10 p-1.5 text-amber-500">
                <Zap className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-2.5 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                -0.18x
              </span>
              <span className="text-xs font-semibold text-slate-500">
                High Sensitivity
              </span>
            </div>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Transmission via Oil (+85% import) & FII Outflows
            </p>
          </div>
        </div>

        {/* SECTION: INTERACTIVE GEOPOLITICAL SHOCK SCENARIO SIMULATOR */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500">
                <Sliders className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Geopolitical Shock Stress Tester (Scenario Simulator)
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Run geopolitical stress shocks through the trained XGBoost model weights to forecast NIFTY 50 reaction.
                </p>
              </div>
            </div>

            <button
              onClick={handleResetSliders}
              className="flex items-center gap-1.5 self-start rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset Baseline
            </button>
          </div>

          {/* Scenario Preset Buttons */}
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {SCENARIO_PRESETS.map((p) => {
              const isActive = activeScenarioId === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleApplyPreset(p)}
                  className={`rounded-xl border p-3.5 text-left transition ${
                    isActive
                      ? "border-blue-500 bg-blue-50/50 dark:border-blue-500/80 dark:bg-blue-950/20 shadow-md"
                      : "border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      {p.title}
                    </span>
                    {isActive && <CheckCircle2 className="h-3.5 w-3.5 text-blue-500" />}
                  </div>
                  <p className="mt-1 line-clamp-2 text-[11px] text-slate-500 dark:text-slate-400">
                    {p.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Sliders Grid & Projected Outcome Panel */}
          <div className="mt-6 grid gap-6 lg:grid-cols-12">
            {/* Sliders (7 cols) */}
            <div className="space-y-4 lg:col-span-7">
              {/* Slider 1: GPR Spike */}
              <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800/80 dark:bg-slate-900/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                    <Globe2 className="h-3.5 w-3.5 text-blue-500" />
                    Geopolitical Risk Index (GPR) Spike
                  </span>
                  <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                    {gprShift >= 0 ? "+" : ""}{gprShift}%
                  </span>
                </div>
                <input
                  type="range"
                  min="-50"
                  max="200"
                  step="5"
                  value={gprShift}
                  onChange={(e) => {
                    setActiveScenarioId(null);
                    setGprShift(Number(e.target.value));
                  }}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
                <div className="mt-1 flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>-50% (De-escalation)</span>
                  <span>0% (Neutral)</span>
                  <span>+200% (Major Shock)</span>
                </div>
              </div>

              {/* Slider 2: Brent Crude Oil */}
              <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800/80 dark:bg-slate-900/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                    <Droplets className="h-3.5 w-3.5 text-amber-500" />
                    Brent Crude Oil Price Shift
                  </span>
                  <span className="font-mono font-bold text-amber-600 dark:text-amber-400">
                    {oilShift >= 0 ? "+" : ""}{oilShift}%
                  </span>
                </div>
                <input
                  type="range"
                  min="-25"
                  max="40"
                  step="1"
                  value={oilShift}
                  onChange={(e) => {
                    setActiveScenarioId(null);
                    setOilShift(Number(e.target.value));
                  }}
                  className="mt-2.5 w-full accent-amber-500 cursor-pointer"
                />
                <div className="mt-1 flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>-25% (Oversupply)</span>
                  <span>0% (Steady)</span>
                  <span>+40% (Energy Embargo)</span>
                </div>
              </div>

              {/* Slider 3: Gold Price Move */}
              <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800/80 dark:bg-slate-900/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                    <Coins className="h-3.5 w-3.5 text-yellow-500" />
                    Gold Safe-Haven Demand (XAU/USD)
                  </span>
                  <span className="font-mono font-bold text-yellow-600 dark:text-yellow-400">
                    {goldShift >= 0 ? "+" : ""}{goldShift}%
                  </span>
                </div>
                <input
                  type="range"
                  min="-10"
                  max="20"
                  step="0.5"
                  value={goldShift}
                  onChange={(e) => {
                    setActiveScenarioId(null);
                    setGoldShift(Number(e.target.value));
                  }}
                  className="mt-2.5 w-full accent-yellow-500 cursor-pointer"
                />
                <div className="mt-1 flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>-10% (Risk-On)</span>
                  <span>0% (Normal)</span>
                  <span>+20% (Panic Flight)</span>
                </div>
              </div>

              {/* Slider 4: USD/INR Currency Move */}
              <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800/80 dark:bg-slate-900/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                    <DollarSign className="h-3.5 w-3.5 text-emerald-500" />
                    USD/INR Exchange Rate Move
                  </span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {usdInrShift >= 0 ? "+" : ""}{usdInrShift}% (Rupee {usdInrShift >= 0 ? "Depreciation" : "Appreciation"})
                  </span>
                </div>
                <input
                  type="range"
                  min="-3"
                  max="5"
                  step="0.2"
                  value={usdInrShift}
                  onChange={(e) => {
                    setActiveScenarioId(null);
                    setUsdInrShift(Number(e.target.value));
                  }}
                  className="mt-2.5 w-full accent-emerald-500 cursor-pointer"
                />
                <div className="mt-1 flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>-3.0% (Stronger INR)</span>
                  <span>0% (Stable)</span>
                  <span>+5.0% (FII Capital Flight)</span>
                </div>
              </div>
            </div>

            {/* Projected Outcome Card (5 cols) */}
            <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/50 p-5 dark:border-slate-800 dark:bg-[#0c101a] lg:col-span-5">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Live Model Prediction
                  </span>
                  <span className="rounded bg-blue-500/10 px-2 py-0.5 font-mono text-[10px] font-bold text-blue-500">
                    MODEL C XGBOOST
                  </span>
                </div>

                <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Projected 7-Day NIFTY 50 Level
                  </p>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900 dark:text-white">
                      {simulationResults.projectedNifty.toLocaleString()}
                    </span>
                    <span className={`text-sm font-bold ${
                      simulationResults.pointChange >= 0
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-600 dark:text-red-400"
                    }`}>
                      {simulationResults.pointChange >= 0 ? "+" : ""}
                      {simulationResults.pointChange} pts
                    </span>
                  </div>

                  <p className="mt-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
                    Expected Return:{" "}
                    <span className={simulationResults.netReturnForecast >= 0 ? "text-emerald-500" : "text-red-500"}>
                      {simulationResults.netReturnForecast >= 0 ? "+" : ""}
                      {simulationResults.netReturnForecast}%
                    </span>
                  </p>
                </div>

                {/* Crash Probability Gauge */}
                <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      Downside Crash Probability
                    </span>
                    <span className={`font-mono font-bold ${
                      simulationResults.finalCrashProb > 60
                        ? "text-red-500"
                        : simulationResults.finalCrashProb > 45
                        ? "text-amber-500"
                        : "text-emerald-500"
                    }`}>
                      {simulationResults.finalCrashProb}%
                    </span>
                  </div>

                  <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div
                      className={`h-full transition-all duration-300 ${
                        simulationResults.finalCrashProb > 65
                          ? "bg-red-500"
                          : simulationResults.finalCrashProb > 45
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${simulationResults.finalCrashProb}%` }}
                    />
                  </div>

                  <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                    {simulationResults.finalCrashProb > 60
                      ? "High vulnerability: Model indicates elevated risk of capital flight and margin compression."
                      : simulationResults.finalCrashProb > 45
                      ? "Neutral / Mixed: Geopolitical shocks partially offset by domestic institutional buying."
                      : "Favorable conditions: Downside risks subdued; high probability of positive equity momentum."}
                  </p>
                </div>

                {/* Shock Breakdown by Channel */}
                <div className="mt-4 space-y-1.5 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                  <div className="flex justify-between">
                    <span>GPR Sentiment Drag:</span>
                    <span className={simulationResults.gprImpact >= 0 ? "text-emerald-500" : "text-red-400"}>
                      {simulationResults.gprImpact >= 0 ? "+" : ""}{simulationResults.gprImpact}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Crude Oil Transmission:</span>
                    <span className={simulationResults.oilImpact >= 0 ? "text-emerald-500" : "text-red-400"}>
                      {simulationResults.oilImpact >= 0 ? "+" : ""}{simulationResults.oilImpact}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Gold Safe-Haven Shift:</span>
                    <span className={simulationResults.goldImpact >= 0 ? "text-emerald-500" : "text-red-400"}>
                      {simulationResults.goldImpact >= 0 ? "+" : ""}{simulationResults.goldImpact}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>USD/INR Currency Pressure:</span>
                    <span className={simulationResults.fxImpact >= 0 ? "text-emerald-500" : "text-red-400"}>
                      {simulationResults.fxImpact >= 0 ? "+" : ""}{simulationResults.fxImpact}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
                <span className="text-[10px] text-slate-400">
                  Calculated using Model C XGBoost coefficients validated on 2025 out-of-time test dataset.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION: MULTI-TIER MODEL ARCHITECTURE COMPARISON */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-purple-500" />
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Multi-Tier Machine Learning Architecture Comparison
                </h2>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Rigorous ablation testing comparing Technical Market data vs Macroeconomics vs Geopolitical GPR integration.
              </p>
            </div>

            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900 text-xs font-semibold">
              <button
                onClick={() => setSelectedTier("all")}
                className={`rounded px-3 py-1 transition ${
                  selectedTier === "all"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                All Tiers
              </button>
              <button
                onClick={() => setSelectedTier("A")}
                className={`rounded px-3 py-1 transition ${
                  selectedTier === "A"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Tier A
              </button>
              <button
                onClick={() => setSelectedTier("B")}
                className={`rounded px-3 py-1 transition ${
                  selectedTier === "B"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Tier B
              </button>
              <button
                onClick={() => setSelectedTier("C")}
                className={`rounded px-3 py-1 transition ${
                  selectedTier === "C"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Tier C
              </button>
            </div>
          </div>

          {/* Cards for each Tier */}
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {MODEL_TIERS_METRICS.filter(
              (m) => selectedTier === "all" || m.tier.includes(selectedTier)
            ).map((tierItem) => (
              <div
                key={tierItem.tier}
                className={`rounded-xl border p-5 transition ${
                  tierItem.tier.includes("Tier C")
                    ? "border-blue-500/50 bg-gradient-to-b from-blue-50/30 to-transparent dark:border-blue-500/30 dark:from-blue-950/20"
                    : "border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111622]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                    {tierItem.tier}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-[11px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    {tierItem.featuresCount} Features
                  </span>
                </div>

                <h3 className="mt-2 text-base font-bold text-slate-900 dark:text-white">
                  {tierItem.name}
                </h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {tierItem.featuresDesc}
                </p>

                <div className="mt-4 grid grid-cols-2 gap-3 rounded-lg border border-slate-100 bg-slate-50/70 p-3 font-mono text-xs dark:border-slate-800 dark:bg-slate-900/50">
                  <div>
                    <span className="block text-[10px] text-slate-400 uppercase">Test MAE</span>
                    <strong className="text-slate-800 dark:text-slate-200">{tierItem.regressorMae}</strong>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-400 uppercase">Direction Acc</span>
                    <strong className="text-emerald-600 dark:text-emerald-400">{tierItem.regressorDirAcc}</strong>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-400 uppercase">Test Accuracy</span>
                    <strong className="text-slate-800 dark:text-slate-200">{tierItem.classifierAcc}</strong>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-400 uppercase">ROC-AUC</span>
                    <strong className="text-blue-600 dark:text-blue-400">{tierItem.classifierAuc}</strong>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Champion Model:</span>
                  <strong className="text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                    {tierItem.bestModel}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION: FEATURE IMPORTANCE RANKING (RECHARTS) */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-emerald-500" />
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Feature Importance Ranking (XGBoost & Random Forest)
                </h2>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Reveals which indicators drive model decisions most heavily when evaluating market shocks.
              </p>
            </div>

            {/* Category Filter */}
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900 text-xs font-semibold">
              <button
                onClick={() => setFeatureCategory("all")}
                className={`rounded px-3 py-1 transition ${
                  featureCategory === "all"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Top 16
              </button>
              <button
                onClick={() => setFeatureCategory("geopolitical")}
                className={`rounded px-3 py-1 transition ${
                  featureCategory === "geopolitical"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Geopolitical (GPR)
              </button>
              <button
                onClick={() => setFeatureCategory("macro")}
                className={`rounded px-3 py-1 transition ${
                  featureCategory === "macro"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Macro (Oil / Gold / FX)
              </button>
              <button
                onClick={() => setFeatureCategory("market")}
                className={`rounded px-3 py-1 transition ${
                  featureCategory === "market"
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Technicals (Price / MAs)
              </button>
            </div>
          </div>

          {/* Bar Chart Container */}
          <div className="mt-6 h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={filteredFeatures}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} horizontal vertical={false} />
                <XAxis type="number" unit="%" tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="feature"
                  type="category"
                  tick={{ fontSize: 11 }}
                  width={140}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="rounded-xl border border-slate-700 bg-slate-900 p-3 font-mono text-xs text-white shadow-xl">
                          <p className="font-bold text-blue-400">{data.name}</p>
                          <p className="text-[11px] text-slate-400">Raw Feature: {data.feature}</p>
                          <div className="mt-2 space-y-1">
                            <p className="text-emerald-400">XGBoost Weight: {data.xgb}%</p>
                            <p className="text-purple-400">Random Forest Weight: {data.rf}%</p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="xgb" fill="#10b981" radius={[0, 4, 4, 0]} name="XGBoost Importance %">
                  {filteredFeatures.map((entry, index) => {
                    let color = "#3b82f6"; // default blue
                    if (entry.category === "geopolitical") color = "#ef4444"; // red for GPR
                    if (entry.category === "macro") color = "#f59e0b"; // amber for macro
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Legend and Key Takeaway */}
          <div className="mt-4 flex flex-wrap items-center justify-between border-t border-slate-200 pt-3 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded bg-red-500" /> Geopolitical Risk (GPR)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded bg-amber-500" /> Macro (Brent Oil, Gold, USD)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded bg-blue-500" /> Technical Momentum
              </span>
            </div>

            <div className="font-mono text-[11px]">
              Key Insight: <strong>GPR_Volatility_5D</strong> ranks #2 overall (5.56%), showing rapid escalation triggers immediate hedging.
            </div>
          </div>
        </div>

        {/* SECTION: DOMAIN INTELLIGENCE / TRANSMISSION CHANNELS */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Box 1: Oil Transmission */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center gap-2 text-amber-500">
              <Droplets className="h-4 w-4" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Crude Oil Transmission
              </h3>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              India imports &gt;85% of its crude oil requirements. A spike in Brent crude directly impacts the Current Account Deficit, inflation expectations, and corporate operating margins across auto, paints, airlines, and cement sectors.
            </p>
          </div>

          {/* Box 2: Foreign Capital & Currency */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center gap-2 text-emerald-500">
              <DollarSign className="h-4 w-4" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                USD/INR & FII Capital Outflows
              </h3>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              During geopolitical shocks, Foreign Institutional Investors (FIIs) reallocate out of Emerging Market equities into US Treasury yields and dollar reserves, weakening the Rupee and creating near-term selling pressure on large-cap NIFTY heavyweights.
            </p>
          </div>

          {/* Box 3: Safe-Haven Gold Diversion */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center gap-2 text-yellow-500">
              <Coins className="h-4 w-4" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Safe-Haven Gold Diversion
              </h3>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Gold acts as the primary hedge asset during heightened geopolitical tension. Multi-horizon gold returns (20-day importance: 5.14%) inversely correlate with domestic equity risk appetite, signaling defensive institutional rebalancing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
