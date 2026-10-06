"use client";

import { useState } from "react";
import { useAnalysis } from "@/context/AnalysisContext";
import {
  Activity,
  ArrowUpRight,
  Compass,
  Filter,
  Globe2,
  Info,
  Layers,
  Link2,
  Network as NetworkIcon,
  Radio,
  Share2,
  Shield,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";

interface RelationshipNode {
  id: string;
  country: string;
  code: string;
  type: "Strategic" | "Trade" | "Economic" | "Security";
  strength: "High" | "Moderate" | "Guarded";
  score: number;
  x: number; // percentage in svg
  y: number;
  color: string;
  flag: string;
  description: string;
}

export default function NetworkPage() {
  const { country1, country2 } = useAnalysis();

  const displayCountry1 = country1 || "India";
  const displayCountry2 = country2 || "Pakistan";

  const [filterType, setFilterType] = useState<string>("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("us");

  const nodes: RelationshipNode[] = [
    {
      id: "us",
      country: "United States",
      code: "US",
      type: "Strategic",
      strength: "High",
      score: 84,
      x: 22,
      y: 25,
      color: "#3b82f6",
      flag: "🇺🇸",
      description: "Major bilateral defense partnership, joint naval exercises, and critical tech exchange.",
    },
    {
      id: "cn",
      country: "China",
      code: "CN",
      type: "Trade",
      strength: "High",
      score: 79,
      x: 78,
      y: 24,
      color: "#06b6d4",
      flag: "🇨🇳",
      description: "Key industrial merchandise supplier; critical manufacturing component supply dependencies.",
    },
    {
      id: "ru",
      country: "Russia",
      code: "RU",
      type: "Strategic",
      strength: "Moderate",
      score: 63,
      x: 18,
      y: 72,
      color: "#8b5cf6",
      flag: "🇷🇺",
      description: "Legacy military hardware maintenance, nuclear energy cooperation, and crude discounts.",
    },
    {
      id: "uae",
      country: "United Arab Emirates",
      code: "UAE",
      type: "Economic",
      strength: "Moderate",
      score: 57,
      x: 82,
      y: 74,
      color: "#10b981",
      flag: "🇦🇪",
      description: "Comprehensive economic partnership, Gulf maritime transit hub, and sovereign wealth investment.",
    },
    {
      id: "c2",
      country: displayCountry2,
      code: displayCountry2.slice(0, 3).toUpperCase(),
      type: "Security",
      strength: "Moderate",
      score: 68,
      x: 50,
      y: 86,
      color: "#f59e0b",
      flag: "⚠️",
      description: "Primary bilateral counterpart under active intelligence surveillance and frontier monitoring.",
    },
  ];

  const filteredNodes = filterType === "all" ? nodes : nodes.filter((n) => n.type.toLowerCase() === filterType.toLowerCase());

  const activeNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  return (
    <div className="relative min-h-[calc(100vh-76px)] overflow-hidden p-6 lg:p-8">
      {/* Background Ambient Glow */}
      <div className="pointer-events-none absolute inset-0 z-0 select-none overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-25 dark:opacity-15 transition-opacity"
          style={{ backgroundImage: `url('/images/tactical_map_bg.jpg')` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#edf2f6]/90 via-[#edf2f6]/85 to-[#edf2f6] dark:from-[#0a0d14]/90 dark:via-[#0a0d14]/90 dark:to-[#0a0d14]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-600/10 via-transparent to-transparent" />
      </div>

      <div className="relative z-10 mx-auto max-w-[1550px] space-y-6">

        {/* Page Header */}
        <div className="flex flex-col gap-4 rounded-3xl border border-slate-200/80 bg-white/85 p-6 shadow-xl backdrop-blur-xl transition dark:border-white/10 dark:bg-[#0e1424]/85 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-blue-500 animate-ping" />
              <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                Relationship Intelligence & Network Topology
              </p>
            </div>

            <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-900 dark:text-white sm:text-3xl">
              Country Relationship Network
            </h1>

            <p className="mt-1 max-w-2xl text-xs text-slate-600 dark:text-slate-300">
              Explore multi-tier strategic alignments, trade dependencies, and security alliances surrounding the selected sovereign pair.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-2.5 text-left shadow-sm backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Primary Pair
              </p>
              <p className="text-xs font-black text-slate-800 dark:text-white">
                {displayCountry1} <span className="text-blue-500 font-mono">↔</span> {displayCountry2}
              </p>
            </div>
          </div>
        </div>

        {/* Top Metric Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="group rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-md transition hover:shadow-md dark:border-white/5 dark:bg-[#111728]/80">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Connected Countries
              </span>
              <div className="rounded-xl bg-blue-500/10 p-2 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
                <Globe2 className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-3xl font-black text-slate-900 dark:text-white">
              24
            </p>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
              Sovereign multilateral links
            </p>
          </div>

          <div className="group rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-md transition hover:shadow-md dark:border-white/5 dark:bg-[#111728]/80">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Strategic Links
              </span>
              <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                <Link2 className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-3xl font-black text-slate-900 dark:text-white">
              8
            </p>
            <p className="mt-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">
              High-confidence treaty pacts
            </p>
          </div>

          <div className="group rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-md transition hover:shadow-md dark:border-white/5 dark:bg-[#111728]/80">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Trade Links
              </span>
              <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-600 dark:bg-cyan-500/20 dark:text-cyan-400">
                <Activity className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-3xl font-black text-slate-900 dark:text-white">
              12
            </p>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
              Major cargo & freight routes
            </p>
          </div>

          <div className="group rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-md transition hover:shadow-md dark:border-white/5 dark:bg-[#111728]/80">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Sensitive Links
              </span>
              <div className="rounded-xl bg-amber-500/10 p-2 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400">
                <ShieldAlert className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-2 text-3xl font-black text-slate-900 dark:text-white">
              4
            </p>
            <p className="mt-1 text-[11px] text-amber-500 font-semibold">
              Under heightened surveillance
            </p>
          </div>
        </div>

        {/* Main Interactive Graph & Right-Hand Signal Telemetry */}
        <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">

          {/* Interactive Topology Graph Section */}
          <section className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-xl backdrop-blur-xl transition dark:border-white/10 dark:bg-[#0e1424]/90">
            {/* Header with Type Filters */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-5">
              <div>
                <div className="flex items-center gap-2">
                  <NetworkIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">
                    Interactive Relationship Topology
                  </h2>
                </div>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                  Click any node to inspect bilateral telemetry and alliance dynamics.
                </p>
              </div>

              {/* Filter Pills */}
              <div className="flex items-center rounded-xl border border-slate-200 bg-slate-50/80 p-1 dark:border-slate-800 dark:bg-slate-900/80">
                {["all", "strategic", "trade", "economic"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilterType(t)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-bold capitalize transition ${
                      filterType === t
                        ? "bg-blue-600 text-white shadow-sm"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Interactive SVG Canvas Area */}
            <div className="relative h-[520px] w-full select-none overflow-hidden rounded-2xl border border-slate-200/70 bg-gradient-to-b from-slate-50/70 to-slate-100/50 dark:border-white/5 dark:from-[#080d18] dark:to-[#040810]">

              {/* SVG Connections and Radial Guidance Rings */}
              <svg className="absolute inset-0 h-full w-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                {/* Concentric Radar Rings */}
                <circle cx="50%" cy="50%" r="120" fill="none" stroke="currentColor" className="text-slate-200/60 dark:text-blue-500/10" strokeDasharray="4 4" strokeWidth="1" />
                <circle cx="50%" cy="50%" r="190" fill="none" stroke="currentColor" className="text-slate-200/40 dark:text-blue-500/5" strokeDasharray="6 6" strokeWidth="1" />

                {/* Connection Lines between Center and Nodes */}
                {nodes.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  const isVisible = filterType === "all" || node.type.toLowerCase() === filterType.toLowerCase();
                  if (!isVisible) return null;

                  return (
                    <g key={node.id}>
                      {/* Base Connection Line */}
                      <line
                        x1="50%"
                        y1="50%"
                        x2={`${node.x}%`}
                        y2={`${node.y}%`}
                        stroke={isSelected ? node.color : "#94a3b8"}
                        strokeWidth={isSelected ? "2.5" : "1.5"}
                        strokeOpacity={isSelected ? "0.9" : "0.35"}
                        strokeDasharray={node.type === "Security" ? "4 4" : undefined}
                      />

                      {/* Animated Pulse Beam along line if selected */}
                      {isSelected && (
                        <circle r="4" fill={node.color}>
                          <animateMotion
                            path={`M ${window?.innerWidth ? (window.innerWidth > 1000 ? 300 : 200) : 250} 260 L ${node.x * 5} ${node.y * 5}`}
                            dur="2s"
                            repeatCount="indefinite"
                          />
                        </circle>
                      )}
                    </g>
                  );
                })}
              </svg>

              {/* Center Sovereign Node (Primary Target) */}
              <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center z-20">
                <div className="relative flex h-24 w-24 items-center justify-center rounded-full border-4 border-blue-500/40 bg-gradient-to-br from-blue-600 to-blue-800 text-white shadow-2xl ring-8 ring-blue-500/15">
                  <Globe2 className="h-9 w-9 text-white animate-spin-slow" />
                  <span className="absolute -bottom-1 rounded-full bg-blue-900 border border-blue-400 px-2 py-0.5 text-[9px] font-black uppercase text-blue-200">
                    NEXUS
                  </span>
                </div>
                <p className="mt-3 text-xs font-black text-slate-900 dark:text-white bg-white/80 dark:bg-slate-900/80 px-2.5 py-0.5 rounded-full border border-slate-200 dark:border-slate-800 shadow-sm">
                  {displayCountry1}
                </p>
              </div>

              {/* Surrounding Nodes */}
              {nodes.map((node) => {
                const isSelected = selectedNodeId === node.id;
                const isVisible = filterType === "all" || node.type.toLowerCase() === filterType.toLowerCase();

                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    style={{ left: `${node.x}%`, top: `${node.y}%` }}
                    className={`group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center z-10 transition-all duration-300 ${
                      !isVisible ? "opacity-20 scale-90 pointer-events-none" : "hover:scale-110"
                    }`}
                  >
                    <div
                      className={`relative flex h-16 w-16 items-center justify-center rounded-2xl border transition-all duration-300 shadow-lg ${
                        isSelected
                          ? "border-blue-500 bg-white ring-4 ring-blue-500/25 dark:bg-slate-800"
                          : "border-slate-200 bg-white hover:border-slate-300 dark:border-white/10 dark:bg-[#111624]"
                      }`}
                    >
                      <span className="text-sm font-black text-slate-800 dark:text-white">
                        {node.code}
                      </span>
                      <span className="absolute -top-1.5 -right-1.5 text-xs">
                        {node.flag}
                      </span>
                      <span
                        className="absolute bottom-1 h-1.5 w-1.5 rounded-full"
                        style={{ backgroundColor: node.color }}
                      />
                    </div>

                    <p className={`mt-1.5 text-[11px] font-bold text-center truncate max-w-[110px] ${
                      isSelected ? "text-blue-600 dark:text-blue-400" : "text-slate-600 dark:text-slate-300"
                    }`}>
                      {node.country}
                    </p>
                    <span className="text-[9px] font-mono text-slate-400 font-semibold">
                      {node.score}/100
                    </span>
                  </button>
                );
              })}

              {/* Bottom Canvas Legend */}
              <div className="absolute bottom-3 left-4 flex items-center gap-3 rounded-xl border border-slate-200/70 bg-white/80 px-3 py-1.5 text-[10px] font-bold shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-slate-900/80">
                <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                  <span className="h-2 w-2 rounded-full bg-blue-500" /> Strategic
                </span>
                <span className="flex items-center gap-1 text-cyan-600 dark:text-cyan-400">
                  <span className="h-2 w-2 rounded-full bg-cyan-500" /> Trade
                </span>
                <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" /> Economic
                </span>
                <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                  <span className="h-2 w-2 rounded-full bg-amber-500" /> Security
                </span>
              </div>
            </div>
          </section>

          {/* Right Panel: Selected Node Inspector & Network Signals */}
          <div className="space-y-6">

            {/* Selected Node Inspector Card */}
            {activeNode && (
              <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-xl backdrop-blur-xl dark:border-white/10 dark:bg-[#0e1424]/90">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-white/5">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{activeNode.flag}</span>
                    <div>
                      <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-600 dark:text-blue-400">
                        {activeNode.type} Partnership
                      </span>
                      <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                        {activeNode.country}
                      </h3>
                    </div>
                  </div>

                  <span
                    className={`rounded-xl px-2.5 py-1 text-xs font-black uppercase ${
                      activeNode.score >= 75
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                        : "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                    }`}
                  >
                    {activeNode.strength}
                  </span>
                </div>

                <div className="my-4 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-center dark:border-white/5 dark:bg-slate-900/50">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Alignment Score</span>
                    <p className="mt-1 text-2xl font-black text-slate-900 dark:text-white">
                      {activeNode.score}<span className="text-xs font-normal text-slate-400">/100</span>
                    </p>
                  </div>

                  <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-center dark:border-white/5 dark:bg-slate-900/50">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nexus Vector</span>
                    <p className="mt-1 font-mono text-sm font-bold text-slate-800 dark:text-slate-200">
                      {displayCountry1} ↔ {activeNode.code}
                    </p>
                  </div>
                </div>

                <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                  {activeNode.description}
                </p>
              </section>
            )}

            {/* Network Signals List */}
            <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-xl backdrop-blur-xl dark:border-white/10 dark:bg-[#0e1424]/90">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                    Network Alignment Signals
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Relative relationship intensity scores
                  </p>
                </div>
                <TrendingUp className="h-4 w-4 text-blue-500" />
              </div>

              <div className="space-y-3">
                {nodes.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  return (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNodeId(node.id)}
                      className={`cursor-pointer rounded-2xl border p-3.5 transition-all duration-200 ${
                        isSelected
                          ? "border-blue-500 bg-blue-50/60 shadow-sm dark:border-blue-500/50 dark:bg-blue-950/20"
                          : "border-slate-100 bg-slate-50/50 hover:border-slate-200 dark:border-white/5 dark:bg-slate-900/40 dark:hover:border-white/10"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span>{node.flag}</span>
                          <div>
                            <p className="text-xs font-bold text-slate-800 dark:text-white">
                              {node.country}
                            </p>
                            <p className="text-[10px] text-slate-400">
                              {node.type} relationship
                            </p>
                          </div>
                        </div>

                        <span className="font-mono text-xs font-black text-slate-800 dark:text-white">
                          {node.score}
                        </span>
                      </div>

                      <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${node.score}%`,
                            backgroundColor: node.color,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        </div>

        {/* Detailed Relationship Roster Table */}
        <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-xl backdrop-blur-xl dark:border-white/10 dark:bg-[#0e1424]/90">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-extrabold text-slate-900 dark:text-white">
                Bilateral Alignment Matrix
              </h2>
              <p className="mt-0.5 text-xs text-slate-400">
                Country-level dependencies and multi-domain strength classifications
              </p>
            </div>
            <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-bold text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
              {nodes.length} Key Nodes
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[650px]">
              <thead>
                <tr className="border-b border-slate-100 text-left dark:border-white/5">
                  <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Sovereign State
                  </th>
                  <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Dominant Vector
                  </th>
                  <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Classification
                  </th>
                  <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Indicator Index
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                {nodes.map((node) => (
                  <tr
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="cursor-pointer transition hover:bg-slate-50/80 dark:hover:bg-slate-800/40"
                  >
                    <td className="px-4 py-3.5 text-xs font-bold text-slate-800 dark:text-white flex items-center gap-2">
                      <span>{node.flag}</span>
                      <span>{node.country}</span>
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-600 dark:text-slate-300">
                      {node.type}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`rounded-lg px-2 py-0.5 text-[10px] font-bold uppercase ${
                          node.strength === "High"
                            ? "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
                            : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {node.strength}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-xs font-black font-mono text-slate-800 dark:text-white">
                      {node.score}/100
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Methodology Footer Card */}
        <section className="rounded-2xl border border-slate-200/80 bg-white/70 p-5 shadow-sm backdrop-blur-md dark:border-white/5 dark:bg-[#111728]/70">
          <div className="flex items-start gap-3">
            <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-xs font-bold text-slate-800 dark:text-white">
                Network Topology Methodology
              </h3>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                Network weights combine historical treaty records, bilateral trading volumes, military hardware dependencies, and voting affinity in multilateral assemblies.
              </p>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}