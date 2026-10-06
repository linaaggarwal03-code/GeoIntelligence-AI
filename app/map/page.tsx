"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { useAnalysis } from "@/context/AnalysisContext";
import {
  Activity,
  Compass,
  Crosshair,
  Flame,
  Globe2,
  Layers,
  MapPinned,
  Maximize2,
  Radio,
  Rotate3D,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Hotspot, HOTSPOTS } from "@/components/map/GlobeView3D";

// Dynamically import 3D Globe View
const GlobeView3D = dynamic(() => import("@/components/map/GlobeView3D"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-[#060911]">
      <div className="text-center">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <p className="mt-3 font-mono text-xs text-blue-400">
          Initializing 3D Geospatial Engine...
        </p>
      </div>
    </div>
  ),
});

// Dynamically import 2D Map View
const MapView = dynamic(() => import("@/components/map/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-slate-100 dark:bg-slate-900">
      <div className="text-center">
        <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
        <p className="mt-3 text-xs text-slate-500">
          Loading 2D map...
        </p>
      </div>
    </div>
  ),
});

export default function MapPage() {
  const { period } = useAnalysis();
  const [mapMode, setMapMode] = useState<"3d" | "2d">("3d");
  const [focusedHotspot, setFocusedHotspot] = useState<Hotspot>(HOTSPOTS[0]);

  const handleSelectHotspot = useCallback((h: Hotspot) => {
    setFocusedHotspot(h);
  }, []);

  return (
    <div className="min-h-full p-6 lg:p-8">
      <div className="mx-auto max-w-[1550px] space-y-6">

        {/* Page Header */}
        <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition dark:border-slate-800 dark:bg-[#111622] lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
                Planetary Geopolitical Surveillance · Live Satellite Feed
              </p>
            </div>

            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Tactical Satellite Map & Planetary Intelligence
            </h1>

            <p className="mt-1 max-w-2xl text-xs text-slate-500 dark:text-slate-400">
              High-resolution satellite tactical reconnaissance tracking militarized zones, maritime flashpoints, kinetic corridors, and defense telemetry across active global theaters.
            </p>
          </div>

          {/* Mode Switcher Pill */}
          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900">
              <button
                type="button"
                onClick={() => setMapMode("2d")}
                className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                  mapMode === "2d"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                Tactical Satellite Map
              </button>

              <button
                type="button"
                onClick={() => setMapMode("3d")}
                className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                  mapMode === "3d"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                }`}
              >
                <Rotate3D className="h-3.5 w-3.5" />
                3D Planetary Globe
              </button>
            </div>
          </div>
        </div>

        {/* Tactical Status Metrics Row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Active Conflict Sectors
              </span>
              <ShieldAlert className="h-4 w-4 text-red-500" />
            </div>
            <p className="mt-2 text-2xl font-extrabold text-slate-800 dark:text-white">
              7 Active Zones
            </p>
            <p className="mt-1 text-[11px] text-red-500 font-medium">
              2 Code-Red Kinetic Flashpoints
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Peak Exposure Index
              </span>
              <TrendingUp className="h-4 w-4 text-amber-500" />
            </div>
            <p className="mt-2 text-2xl font-extrabold text-amber-500">
              92 / 100
            </p>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Eastern Europe (Donbas / Black Sea)
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Corridor Chokepoints
              </span>
              <Radio className="h-4 w-4 text-blue-500" />
            </div>
            <p className="mt-2 text-2xl font-extrabold text-slate-800 dark:text-white">
              Hormuz & Bab-el-Mandeb
            </p>
            <p className="mt-1 text-[11px] text-blue-500 font-medium">
              34% Global Oil Flow at Risk
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Telemetric Sensor Mode
              </span>
              <Activity className="h-4 w-4 text-emerald-500" />
            </div>
            <p className="mt-2 text-2xl font-extrabold text-emerald-500">
              Real-Time Feed
            </p>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Synchronized 60 FPS WebGL
            </p>
          </div>
        </div>

        {/* Main Map / Globe Viewport */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-[#060911]">
          {/* Top Bar inside Map Canvas */}
          <div className="flex items-center justify-between border-b border-slate-200/80 bg-slate-50/70 px-5 py-3 dark:border-white/10 dark:bg-[#0c121e]">
            <div className="flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-bold text-slate-800 dark:text-white">
                {mapMode === "3d" ? "3D Planetary Tactical Projection" : "High-Resolution Tactical Satellite Reconnaissance"}
              </span>
              <span className={`rounded px-2 py-0.5 text-[10px] font-semibold ${
                mapMode === "3d"
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300"
                  : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
              }`}>
                {mapMode === "3d" ? "INTERACTIVE 3D · ROTATE & ZOOM" : "ESRI WORLD SATELLITE · ACTIVE THEATERS"}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
              <span className="hidden sm:inline">Active Target:</span>
              <strong className="text-slate-800 dark:text-white">{focusedHotspot.name}</strong>
            </div>
          </div>

          {/* Viewport Container */}
          <div className="relative isolate h-[720px] w-full">
            {mapMode === "3d" ? (
              <GlobeView3D
                onSelectHotspot={handleSelectHotspot}
                onSwitchTo2D={() => setMapMode("2d")}
              />
            ) : (
              <div className="h-full w-full">
                <MapView onBackToOrbit={() => setMapMode("3d")} />
              </div>
            )}
          </div>
        </section>

        {/* Hotspots Reference Grid & Methodology */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Monitored Hotspots Table */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  Global Flashpoint Directory
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Real-time threat indices and territorial conflict monitoring.
                </p>
              </div>
              <Compass className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800/80 overflow-x-auto">
              {HOTSPOTS.map((h) => {
                const isSelected = focusedHotspot.id === h.id;
                return (
                  <div
                    key={h.id}
                    onClick={() => setFocusedHotspot(h)}
                    className={`flex cursor-pointer items-center justify-between py-3 px-2 rounded-lg transition ${
                      isSelected
                        ? "bg-blue-50/80 dark:bg-blue-950/30"
                        : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          h.score >= 85
                            ? "bg-red-500 animate-pulse"
                            : h.score >= 75
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                        }`}
                      />
                      <div>
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                          {h.name}
                        </p>
                        <p className="text-[10px] text-slate-400 font-mono">
                          {h.actor1} vs {h.actor2}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">
                        {h.score}/100
                      </span>
                      <span
                        className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${
                          h.score >= 85
                            ? "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300"
                            : h.score >= 75
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                        }`}
                      >
                        {h.risk}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tactical Legend & Methodology */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-[#111622] space-y-5">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Tactical 3D Symbology
              </h2>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Guide to visual telemetry rendered in the 3D sphere.
              </p>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-start gap-2.5 rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-900/50">
                <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-red-500 animate-ping" />
                <div>
                  <strong className="text-slate-800 dark:text-slate-200">Pulsing Radar Rings</strong>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    Indicates high kinetic activity or immediate airspace/maritime interdiction danger.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2.5 rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-900/50">
                <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-blue-500" />
                <div>
                  <strong className="text-slate-800 dark:text-slate-200">Geodesic 3D Arcs & Photons</strong>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    Visualizes kinetic flight paths, proxy weapon corridors, and vulnerable maritime supply lines.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2.5 rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-900/50">
                <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-amber-500" />
                <div>
                  <strong className="text-slate-800 dark:text-slate-200">Vertical Light Beacons</strong>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    Beacon height corresponds directly to composite geopolitical risk index (0–100).
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-3 dark:border-blue-900/40 dark:bg-blue-950/20 text-[11px] text-slate-600 dark:text-slate-400">
              <p>
                <strong>Tip:</strong> Drag anywhere on the globe to freely rotate the planet in 3D. Use your mouse scroll wheel to zoom in closer to target theaters. Click on any beacon or target in the HUD to lock sensors.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}