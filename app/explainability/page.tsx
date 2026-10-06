"use client";

import { useAnalysis } from "@/context/AnalysisContext";
import {
  Activity,
  ArrowDown,
  ArrowUp,
  BarChart3,
  Info,
  ShieldAlert,
  Target,
} from "lucide-react";

const featureContributions = [
  {
    feature: "Recent Conflict Activity",
    contribution: 18,
    direction: "increase",
    description:
      "Recent event intensity contributes upward pressure to the model output.",
  },
  {
    feature: "Historical Conflict Frequency",
    contribution: 14,
    direction: "increase",
    description:
      "Historical conflict patterns indicate elevated baseline risk.",
  },
  {
    feature: "Trade Exposure",
    contribution: 9,
    direction: "increase",
    description:
      "Higher bilateral economic exposure increases sensitivity to disruption.",
  },
  {
    feature: "Political Stability",
    contribution: -7,
    direction: "decrease",
    description:
      "Relative political stability offsets part of the upward pressure.",
  },
  {
    feature: "Economic Growth",
    contribution: -5,
    direction: "decrease",
    description:
      "Stronger economic conditions slightly reduce the estimated impact.",
  },
];

const modelMetrics = [
  {
    label: "Baseline Indicator",
    value: "52",
    description: "Current model output",
  },
  {
    label: "Top Positive Factor",
    value: "+18",
    description: "Recent conflict activity",
  },
  {
    label: "Top Negative Factor",
    value: "-7",
    description: "Political stability",
  },
  {
    label: "Features Used",
    value: "24",
    description: "Model input variables",
  },
];

export default function ExplainabilityPage() {
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
              <Activity className="h-4 w-4 text-blue-600" />

              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600">
                Model Transparency
              </p>
            </div>

            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Explainability
            </h1>

            <p className="mt-1.5 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
              Understand which factors are contributing to the current
              geopolitical and economic model output.
            </p>
          </div>

        </div>

        {/* Model summary */}
        <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {modelMetrics.map((metric, index) => (
            <div
              key={metric.label}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  {metric.label}
                </p>

                {index === 0 ? (
                  <Target className="h-4 w-4 text-blue-500" />
                ) : index === 1 ? (
                  <ArrowUp className="h-4 w-4 text-red-500" />
                ) : index === 2 ? (
                  <ArrowDown className="h-4 w-4 text-emerald-500" />
                ) : (
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                )}
              </div>

              <p className="mt-2 text-2xl font-semibold text-slate-800">
                {metric.value}
              </p>

              <p className="mt-1 text-[11px] text-slate-500">
                {metric.description}
              </p>
            </div>
          ))}
        </div>

        {/* Main explanation */}
        <div className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
          {/* Feature contributions */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Feature Contributions
                </h2>

                <p className="mt-1 text-[11px] text-slate-400">
                  Factors influencing the current model output
                </p>
              </div>

              <span className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-[10px] text-slate-500">
                SHAP-style explanation
              </span>
            </div>

            <div className="mt-6 space-y-5">
              {featureContributions.map((item) => {
                const positive = item.contribution > 0;
                const absoluteValue = Math.abs(item.contribution);

                return (
                  <div key={item.feature}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${
                              positive
                                ? "bg-red-50 text-red-500"
                                : "bg-emerald-50 text-emerald-600"
                            }`}
                          >
                            {positive ? (
                              <ArrowUp className="h-3.5 w-3.5" />
                            ) : (
                              <ArrowDown className="h-3.5 w-3.5" />
                            )}
                          </span>

                          <p className="text-xs font-semibold text-slate-700">
                            {item.feature}
                          </p>
                        </div>

                        <p className="mt-1.5 pl-8 text-[10px] leading-4 text-slate-400">
                          {item.description}
                        </p>
                      </div>

                      <span
                        className={`shrink-0 text-sm font-semibold ${
                          positive
                            ? "text-red-500"
                            : "text-emerald-600"
                        }`}
                      >
                        {positive ? "+" : ""}
                        {item.contribution}
                      </span>
                    </div>

                    <div className="mt-3 pl-8">
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full transition-all ${
                            positive
                              ? "bg-red-400"
                              : "bg-emerald-400"
                          }`}
                          style={{
                            width: `${absoluteValue * 3.2}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Current output */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Current Model Output
              </h2>

              <p className="mt-1 text-[11px] text-slate-400">
                Interpreting the selected analysis
              </p>
            </div>

            <div className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/50 p-5">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-medium uppercase tracking-wider text-blue-600">
                  Conflict / Escalation Indicator
                </p>

                <ShieldAlert className="h-4 w-4 text-blue-600" />
              </div>

              <div className="mt-3 flex items-end gap-3">
                <span className="text-5xl font-semibold tracking-tight text-slate-800">
                  52
                </span>

                <span className="mb-2 text-xs text-slate-500">
                  / 100
                </span>
              </div>

              <div className="mt-5 h-2 overflow-hidden rounded-full bg-blue-100">
                <div
                  className="h-full rounded-full bg-blue-600"
                  style={{ width: "52%" }}
                />
              </div>

              <div className="mt-3 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">
                  Lower
                </span>

                <span className="text-[10px] font-medium text-slate-500">
                  Elevated sensitivity
                </span>

                <span className="text-[10px] text-slate-400">
                  Higher
                </span>
              </div>
            </div>

            {/* Interpretation */}
            <div className="mt-5 rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-xs font-semibold text-slate-700">
                Model interpretation
              </p>

              <p className="mt-2 text-[11px] leading-5 text-slate-500">
                The current output is primarily influenced by recent
                conflict activity and historical conflict frequency.
                Political stability and economic conditions provide
                partially offsetting signals.
              </p>
            </div>

            {/* Horizon */}
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-100 bg-white p-3">
                <p className="text-[9px] uppercase tracking-wider text-slate-400">
                  Horizon
                </p>

                <p className="mt-1 text-xs font-semibold text-slate-700">
                  {period || "90"} days
                </p>
              </div>

              <div className="rounded-xl border border-slate-100 bg-white p-3">
                <p className="text-[9px] uppercase tracking-wider text-slate-400">
                  Features
                </p>

                <p className="mt-1 text-xs font-semibold text-slate-700">
                  24 variables
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Positive vs negative */}
        <div className="mt-5 grid gap-5 md:grid-cols-2">
          {/* Increasing */}
          <section className="rounded-2xl border border-red-100 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50">
                <ArrowUp className="h-4 w-4 text-red-500" />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Factors Increasing the Indicator
                </h2>

                <p className="mt-1 text-[10px] text-slate-400">
                  Upward pressure on the model output
                </p>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {featureContributions
                .filter((item) => item.contribution > 0)
                .map((item) => (
                  <div
                    key={item.feature}
                    className="flex items-center justify-between rounded-lg bg-red-50/50 px-3 py-2.5"
                  >
                    <span className="text-xs text-slate-600">
                      {item.feature}
                    </span>

                    <span className="text-xs font-semibold text-red-500">
                      +{item.contribution}
                    </span>
                  </div>
                ))}
            </div>
          </section>

          {/* Decreasing */}
          <section className="rounded-2xl border border-emerald-100 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                <ArrowDown className="h-4 w-4 text-emerald-600" />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-slate-800">
                  Factors Reducing the Indicator
                </h2>

                <p className="mt-1 text-[10px] text-slate-400">
                  Downward pressure on the model output
                </p>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {featureContributions
                .filter((item) => item.contribution < 0)
                .map((item) => (
                  <div
                    key={item.feature}
                    className="flex items-center justify-between rounded-lg bg-emerald-50/50 px-3 py-2.5"
                  >
                    <span className="text-xs text-slate-600">
                      {item.feature}
                    </span>

                    <span className="text-xs font-semibold text-emerald-600">
                      {item.contribution}
                    </span>
                  </div>
                ))}
            </div>
          </section>
        </div>

        {/* Explanation methodology */}
        <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <Info className="h-4 w-4 text-blue-600" />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                Explainable AI Methodology
              </h2>

              <p className="mt-1 text-[11px] leading-5 text-slate-500">
                The production system will use SHAP values to explain
                individual model predictions. Positive contributions
                indicate features pushing the prediction upward, while
                negative contributions indicate features pushing it
                downward. Explanations will be generated from the actual
                trained model rather than manually assigned weights.
              </p>
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[10px] leading-5 text-slate-500">
            Explainability describes model behavior and does not establish
            causality. A feature contribution should be interpreted as
            evidence of how the model used the available information, not
            as proof that the feature directly caused the geopolitical
            outcome.
          </p>
        </section>
      </div>
    </div>
  );
}