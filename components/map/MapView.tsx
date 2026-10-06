"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import "leaflet/dist/leaflet.css";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowUp,
  Compass,
  Crosshair,
  ExternalLink,
  Flame,
  Globe2,
  Info,
  Layers,
  MapPin,
  Menu,
  Minimize2,
  Newspaper,
  Radio,
  RotateCcw,
  Search,
  Shield,
  ShieldAlert,
  Volume2,
  X,
  Zap,
} from "lucide-react";

// Fix for default Leaflet icon paths in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

const MapContainerComponent = MapContainer as any;
const TileLayerComponent = TileLayer as any;
const MarkerComponent = Marker as any;
const PopupComponent = Popup as any;


export interface BaseLocation {
  id: string;
  name: string;
  lat: number;
  lng: number;
  type: "base" | "flashpoint" | "reef" | "outpost";
  intensity: "high" | "medium" | "low" | "watch";
  details: string;
  isMainTarget?: boolean;
}

export interface Theater {
  id: string;
  name: string;
  shortName: string;
  region: string;
  center: [number, number];
  zoom: number;
  status: "ACTIVE · HIGH" | "ELEVATED" | "CRITICAL" | "WATCH";
  intensity: "high" | "medium" | "low" | "watch";
  headline: {
    source: string;
    text: string;
  };
  keyBasesCount: number;
  coordinates: string;
  summary: string;
  bases: BaseLocation[];
}

export const THEATERS: Theater[] = [
  {
    id: "south-china-sea",
    name: "South China Sea Disputes",
    shortName: "SOUTH CHINA SEA DISPUTES",
    region: "ASIA-PACIFIC",
    center: [13.2, 114.2],
    zoom: 5.5,
    status: "ACTIVE · HIGH",
    intensity: "medium",
    headline: {
      source: "JAPAN TIMES",
      text: "Chinese work gathering pace on Antelope Reef in South China Sea; radar surveillance platforms reinforced.",
    },
    keyBasesCount: 8,
    coordinates: "LAT 12.2°N · LNG 114.3°E",
    summary:
      "Contested maritime Exclusive Economic Zones, militarized artificial islands, regular air-sea confrontations, and semiconductor transport chokepoint monitoring across the First Island Chain.",
    bases: [
      {
        id: "woody",
        name: "WOODY ISLAND (YONGXING) BASE",
        lat: 16.83,
        lng: 112.33,
        type: "base",
        intensity: "high",
        details: "Primary military headquarters in Paracels. Runway: 2,700m. HQ-9 surface-to-air missile batteries active.",
      },
      {
        id: "scarborough",
        name: "SCARBOROUGH SHOAL",
        lat: 15.15,
        lng: 117.75,
        type: "reef",
        intensity: "watch",
        details: "Contested lagoon. Persistent China Coast Guard blockades against Philippine fishing flotillas.",
      },
      {
        id: "scs-main",
        name: "SOUTH CHINA SEA DISPUTES",
        lat: 12.5,
        lng: 114.2,
        type: "flashpoint",
        intensity: "medium",
        isMainTarget: true,
        details: "Central tactical flashpoint. Freedom of Navigation patrols monitored alongside PLA Navy task forces.",
      },
      {
        id: "itu-aba",
        name: "ITU ABA (TAIPING ISLAND)",
        lat: 10.37,
        lng: 114.36,
        type: "outpost",
        intensity: "high",
        details: "Largest natural Spratly island held by Taiwan Coast Guard. Weather and radar reconnaissance station.",
      },
      {
        id: "mischief",
        name: "MISCHIEF REEF BASE",
        lat: 9.91,
        lng: 115.53,
        type: "base",
        intensity: "high",
        details: "Fortified artificial reef. 2,640m runway, hangars for 24 combat aircraft, high-frequency radar arrays.",
      },
      {
        id: "fiery-cross",
        name: "FIERY CROSS REEF BASE",
        lat: 9.55,
        lng: 112.89,
        type: "base",
        intensity: "high",
        details: "Major communications and early-warning hub. Deep-water harbor berths for guided-missile destroyers.",
      },
      {
        id: "malaysia-reef",
        name: "SWALLOW REEF (LAYANG-LAYANG)",
        lat: 7.37,
        lng: 112.34,
        type: "outpost",
        intensity: "watch",
        details: "Royal Malaysian Navy presence. Marine dive sanctuary and tactical maritime border watch.",
      },
    ],
  },
  {
    id: "myanmar",
    name: "Myanmar Civil War Theater",
    shortName: "MYANMAR CIVIL WAR",
    region: "SOUTHEAST ASIA",
    center: [20.5, 96.2],
    zoom: 6,
    status: "ACTIVE · HIGH",
    intensity: "high",
    headline: {
      source: "REUTERS",
      text: "Resistance forces consolidate perimeter around Shan State trade corridors; junta air sorties intensified.",
    },
    keyBasesCount: 6,
    coordinates: "LAT 21.9°N · LNG 95.9°E",
    summary:
      "Multi-front kinetic conflict between Myanmar Armed Forces (Tatmadaw) and resistance coalitions (PDF / EAOs), with vital border trade gateways to China under contestation.",
    bases: [
      {
        id: "naypyidaw",
        name: "NAYPYIDAW COMMAND HQ",
        lat: 19.76,
        lng: 96.07,
        type: "base",
        intensity: "high",
        details: "Military junta headquarters and central airspace command.",
      },
      {
        id: "mandalay",
        name: "MANDALAY LOGISTICS CORRIDOR",
        lat: 21.97,
        lng: 96.08,
        type: "flashpoint",
        intensity: "high",
        details: "Heavy artillery movements along river transit artery.",
      },
      {
        id: "shan",
        name: "LASHIO / SHAN STATE HIGHWAY",
        lat: 22.96,
        lng: 97.75,
        type: "flashpoint",
        intensity: "high",
        details: "Strategic border checkpoint; Operation 1027 territorial control.",
      },
    ],
  },
  {
    id: "eastern-europe",
    name: "Eastern Europe & Black Sea Theater",
    shortName: "BLACK SEA / UKRAINE FRONT",
    region: "EASTERN EUROPE",
    center: [46.8, 34.5],
    zoom: 6,
    status: "CRITICAL",
    intensity: "high",
    headline: {
      source: "UKRAINSKA PRAVDA",
      text: "Uncrewed surface vessels target deep logistics terminals; air defense intercepts logged across Pokrovsk sector.",
    },
    keyBasesCount: 9,
    coordinates: "LAT 48.4°N · LNG 37.8°E",
    summary:
      "High-tempo kinetic land warfare along the 1,000km frontline, combined with long-range drone strikes on refineries and naval missile standoffs in the Black Sea basin.",
    bases: [
      {
        id: "sevastopol",
        name: "SEVASTOPOL NAVAL BASE",
        lat: 44.61,
        lng: 33.52,
        type: "base",
        intensity: "high",
        details: "Black Sea Fleet homeport under persistent drone and cruise missile alert.",
      },
      {
        id: "donbas",
        name: "POKROVSK FRONT LINE",
        lat: 48.28,
        lng: 37.18,
        type: "flashpoint",
        intensity: "high",
        isMainTarget: true,
        details: "Central logistics node; intense mechanized assault and glide bomb sorties.",
      },
      {
        id: "snake-island",
        name: "SNAKE ISLAND RADAR POST",
        lat: 45.25,
        lng: 30.2,
        type: "outpost",
        intensity: "medium",
        details: "Western Black Sea grain corridor surveillance and electronic warfare station.",
      },
    ],
  },
  {
    id: "middle-east",
    name: "Persian Gulf & Levant Escalation",
    shortName: "STRAIT OF HORMUZ / GULF",
    region: "MIDDLE EAST",
    center: [26.8, 54.5],
    zoom: 6,
    status: "CRITICAL",
    intensity: "high",
    headline: {
      source: "AL JAZEERA",
      text: "Naval task forces monitor Hormuz tanker corridors following retaliatory missile alerts across Levant airspace.",
    },
    keyBasesCount: 7,
    coordinates: "LAT 26.5°N · LNG 56.2°E",
    summary:
      "Chokepoint security for 21M bbl/d crude transit, regional ballistic missile exchanges, electronic jamming, and maritime escort protocols across the Arabian Sea.",
    bases: [
      {
        id: "hormuz",
        name: "STRAIT OF HORMUZ CHOKEPOINT",
        lat: 26.56,
        lng: 56.25,
        type: "flashpoint",
        intensity: "high",
        isMainTarget: true,
        details: "World's most critical oil transit corridor. Vessel GPS spoofing reported.",
      },
      {
        id: "bandar-abbas",
        name: "BANDAR ABBAS IRGC NAVAL BASE",
        lat: 27.18,
        lng: 56.26,
        type: "base",
        intensity: "high",
        details: "Fast-attack missile boat headquarters and drone reconnaissance staging.",
      },
      {
        id: "al-udeid",
        name: "AL UDEID COMBINED AIR CENTER",
        lat: 25.11,
        lng: 51.31,
        type: "base",
        intensity: "medium",
        details: "Forward headquarters of US Central Command; airborne early warning sweeps.",
      },
    ],
  },
];

// Helper to zoom/pan the Leaflet map smoothly
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.6, easeLinearity: 0.25 });
  }, [center, zoom, map]);
  return null;
}

// Function to generate the custom tactical HTML marker icons matching the user's screenshot
function createTacticalIcon(base: BaseLocation) {
  const isHigh = base.intensity === "high";
  const isMed = base.intensity === "medium";
  const isWatch = base.intensity === "watch";

  const colorHex = isHigh ? "#ef4444" : isMed ? "#f97316" : isWatch ? "#38bdf8" : "#22c55e";

  if (base.isMainTarget) {
    // Large Concentric Target Crosshair Reticle with Leader Line & Coral Badge
    return L.divIcon({
      className: "tactical-main-target-marker",
      html: `
        <div style="position: relative; display: flex; align-items: center; pointer-events: auto; cursor: pointer;">
          <!-- Concentric Crosshair Target Reticle -->
          <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <div style="position: absolute; inset: 0; border: 2px solid ${colorHex}; border-radius: 50%; opacity: 0.8; animation: ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="position: absolute; inset: 4px; border: 1.5px solid ${colorHex}; border-radius: 50%; opacity: 0.9;"></div>
            <div style="width: 10px; height: 10px; background-color: ${colorHex}; border-radius: 50%; box-shadow: 0 0 10px ${colorHex};"></div>
            <!-- Crosshair tick marks -->
            <div style="position: absolute; width: 100%; height: 1px; background: ${colorHex}; opacity: 0.7;"></div>
            <div style="position: absolute; height: 100%; width: 1px; background: ${colorHex}; opacity: 0.7;"></div>
          </div>

          <!-- Leader Line -->
          <div style="width: 22px; height: 1.5px; background: ${colorHex}; opacity: 0.8; margin-left: 2px;"></div>

          <!-- Target Callout Badge Pill -->
          <div style="
            background: rgba(18, 24, 38, 0.92);
            border: 1px solid rgba(239, 68, 68, 0.7);
            border-left: 4px solid #ef4444;
            color: #ffffff;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.08em;
            padding: 4px 10px;
            border-radius: 9999px;
            white-space: nowrap;
            box-shadow: 0 4px 18px rgba(0,0,0,0.6);
            display: flex;
            align-items: center;
            gap: 6px;
          ">
            <span>${base.name}</span>
          </div>
        </div>
      `,
      iconSize: [280, 40],
      iconAnchor: [17, 17],
    });
  }

  // Tactical Base Callout Badge with Left Horizontal Leader Line
  return L.divIcon({
    className: "tactical-callout-marker",
    html: `
      <div style="position: relative; display: flex; align-items: center; pointer-events: auto; cursor: pointer;">
        <!-- Glowing Base Anchor Dot -->
        <div style="width: 8px; height: 8px; background-color: ${colorHex}; border-radius: 50%; box-shadow: 0 0 8px ${colorHex}; flex-shrink: 0;"></div>

        <!-- Leader Line -->
        <div style="width: 18px; height: 1px; background: rgba(255,255,255,0.4); margin-left: 1px;"></div>

        <!-- Callout Pill Label with Left Accent Border -->
        <div style="
          background: rgba(12, 17, 29, 0.88);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-left: 3px solid ${colorHex};
          color: #e2e8f0;
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.06em;
          padding: 3px 8px;
          border-radius: 9999px;
          white-space: nowrap;
          box-shadow: 0 2px 10px rgba(0,0,0,0.5);
          backdrop-filter: blur(4px);
        ">
          ${base.name}
        </div>
      </div>
    `,
    iconSize: [240, 30],
    iconAnchor: [4, 15],
  });
}

export default function MapView({ onBackToOrbit }: { onBackToOrbit?: () => void }) {
  const [activeTheater, setActiveTheater] = useState<Theater>(THEATERS[0]);
  const [selectedBase, setSelectedBase] = useState<BaseLocation | null>(THEATERS[0].bases[2] || null);
  const [showClassificationModal, setShowClassificationModal] = useState(false);
  const [showSidePanel, setShowSidePanel] = useState(true);

  // Cycle headlines periodically
  const [newsIndex, setNewsIndex] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => {
      setNewsIndex((prev) => (prev + 1) % THEATERS.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const currentNewsTheater = THEATERS[newsIndex];

  // Handler to switch theater
  const handleSelectTheater = (th: Theater) => {
    setActiveTheater(th);
    const mainTarget = th.bases.find((b) => b.isMainTarget) || th.bases[0];
    setSelectedBase(mainTarget || null);
  };

  // Back to orbit handler: zoom out to global view
  const handleBackToOrbit = () => {
    if (onBackToOrbit) {
      onBackToOrbit();
    } else {
      setActiveTheater({
        ...activeTheater,
        center: [20, 20],
        zoom: 2.5,
      });
    }
  };

  return (
    <div className="relative h-full w-full select-none overflow-hidden rounded-2xl bg-[#060c18] font-sans">

      {/* LEAFLET SATELLITE MAP (ESRI Photorealistic World Imagery) */}
      <MapContainerComponent
        center={activeTheater.center}
        zoom={activeTheater.zoom}
        minZoom={2}
        maxZoom={12}
        scrollWheelZoom={true}
        className="h-full w-full z-0"
        zoomControl={false}
        worldCopyJump
      >
        <MapController center={activeTheater.center} zoom={activeTheater.zoom} />

        {/* High-Resolution ESRI Photorealistic World Imagery Satellite Layer */}
        <TileLayerComponent
          attribution='Imagery: &copy; Esri, NASA, USGS, Blue Marble'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={18}
          maxZoom={18}
        />

        {/* Boundaries & Maritime Places Label Overlay */}
        <TileLayerComponent
          url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={18}
          maxZoom={18}
          opacity={0.65}
        />

        {/* Tactical Markers with Callout Lines directly on Map */}
        {activeTheater.bases.map((base) => (
          <MarkerComponent
            key={base.id}
            position={[base.lat, base.lng]}
            icon={createTacticalIcon(base)}
            eventHandlers={{
              click: () => {
                setSelectedBase(base);
                setShowSidePanel(true);
              },
            }}
          >
            <PopupComponent className="tactical-leaflet-popup">
              <div className="p-1 min-w-[200px]">
                <p className="font-mono text-[10px] font-bold text-red-500 uppercase tracking-widest">
                  {base.type} · {base.intensity}
                </p>
                <h4 className="text-xs font-black text-slate-900 mt-0.5">{base.name}</h4>
                <p className="text-[11px] leading-relaxed text-slate-600 mt-1.5">{base.details}</p>
                <div className="mt-2 text-[10px] font-mono text-slate-400">
                  LAT {base.lat.toFixed(2)}° · LNG {base.lng.toFixed(2)}°
                </div>
              </div>
            </PopupComponent>
          </MarkerComponent>
        ))}
      </MapContainerComponent>

      {/* TOP TACTICAL NAVIGATION BAR (Matches screenshot layout) */}
      <div className="pointer-events-none absolute left-4 right-4 top-4 z-[500] flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Menu button */}
          <button
            onClick={() => setShowSidePanel(!showSidePanel)}
            className="pointer-events-auto flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-[#0e1424]/90 text-white shadow-xl backdrop-blur-md transition hover:bg-white/10"
          >
            <Menu className="h-4 w-4" />
          </button>

          {/* Status pill: 🔴 LIVE · 29 THEATERS · UPDATED 2026-10-06 */}
          <div className="pointer-events-auto flex items-center gap-2 rounded-xl border border-white/15 bg-[#0a0f1d]/90 px-3.5 py-2 text-xs font-bold text-white shadow-2xl backdrop-blur-md">
            <span className="flex h-2 w-2 rounded-full bg-red-500 animate-ping" />
            <span className="font-mono tracking-wider text-[11px]">
              LIVE · 29 THEATERS · UPDATED 2026-10-06
            </span>
          </div>

          {/* Active Theater Quick-Pill Switchers */}
          <div className="pointer-events-auto hidden md:flex items-center gap-1.5">
            {THEATERS.map((t) => {
              const isSelected = activeTheater.id === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => handleSelectTheater(t)}
                  className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-[11px] font-bold tracking-wider transition ${
                    isSelected
                      ? "border-red-500/80 bg-[#161c2e]/95 text-white shadow-md ring-1 ring-red-500/40"
                      : "border-white/10 bg-[#0a0f1d]/85 text-slate-300 hover:bg-white/10"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      t.intensity === "high" ? "bg-red-500" : "bg-amber-400"
                    }`}
                  />
                  <span>{t.shortName}</span>
                  <span className="text-[9px] text-slate-400 font-normal uppercase">
                    {t.status.split("·")[0].trim()}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Top-Right: BACK TO ORBIT button */}
        <button
          onClick={handleBackToOrbit}
          className="pointer-events-auto flex items-center gap-1.5 rounded-xl border border-white/20 bg-[#0e1424]/90 px-3.5 py-2 text-xs font-bold tracking-wider text-white shadow-xl backdrop-blur-md transition hover:bg-white/15 active:scale-95"
        >
          <ArrowUp className="h-3.5 w-3.5 text-blue-400" />
          <span>BACK TO ORBIT</span>
        </button>
      </div>

      {/* FLOATING INTENSITY LEGEND CARD (Matches top-left in screenshot) */}
      <div className="pointer-events-auto absolute left-4 top-18 z-[500] w-[210px] rounded-2xl border border-white/15 bg-[#0b101c]/90 p-4 shadow-2xl backdrop-blur-md">
        <p className="font-mono text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
          INTENSITY
        </p>

        <div className="mt-3 space-y-2 text-xs font-semibold text-slate-200">
          <div className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500 shadow-sm shadow-red-500/50" />
            <span>High intensity</span>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50" />
            <span>Medium / elevated</span>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
            <span>Lower intensity</span>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400 shadow-sm shadow-sky-400/50" />
            <span>Watch / flashpoint</span>
          </div>
        </div>

        <button
          onClick={() => setShowClassificationModal(true)}
          className="mt-3 flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white transition"
        >
          <span>How we classify</span>
          <span className="font-mono">→</span>
        </button>
      </div>

      {/* RIGHT-HAND THEATER DETAIL PANEL (Matches right side of screenshot) */}
      {showSidePanel && (
        <aside className="pointer-events-auto absolute bottom-16 right-4 top-4 z-[500] w-[340px] overflow-y-auto rounded-3xl border border-white/15 bg-[#0c1220]/95 p-5 shadow-2xl backdrop-blur-xl transition-all">
          <div className="flex items-start justify-between border-b border-white/10 pb-4">
            <div>
              <div className="flex flex-wrap items-center gap-1.5 mb-2">
                <span className="rounded-md border border-red-500/40 bg-red-500/20 px-2 py-0.5 font-mono text-[9px] font-extrabold uppercase text-red-400">
                  {activeTheater.status}
                </span>
                <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-[9px] font-bold text-slate-300">
                  {activeTheater.region}
                </span>
              </div>
              <h2 className="text-lg font-black tracking-tight text-white">
                {activeTheater.name}
              </h2>
            </div>

            <button
              onClick={() => setShowSidePanel(false)}
              className="text-slate-400 hover:text-white transition p-1"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Coordinates & Monitored Bases */}
          <div className="my-4 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-xl border border-white/5 bg-white/[0.03] p-2.5">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Position</span>
              <p className="mt-1 font-mono text-[11px] font-bold text-slate-200">
                {activeTheater.coordinates.split("·")[0].trim()}
              </p>
            </div>

            <div className="rounded-xl border border-white/5 bg-white/[0.03] p-2.5">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Recon Bases</span>
              <p className="mt-1 font-mono text-[11px] font-bold text-blue-400">
                {activeTheater.bases.length} Key Positions
              </p>
            </div>
          </div>

          {/* Theater Summary */}
          <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3 text-xs">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Geopolitical Overview
            </p>
            <p className="text-[11px] leading-relaxed text-slate-300">
              {activeTheater.summary}
            </p>
          </div>

          {/* Selected Base / Target Focus Detail */}
          {selectedBase && (
            <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-950/20 p-3.5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[9px] font-extrabold uppercase text-red-400">
                  Selected Target Focus
                </span>
                <span className="rounded bg-red-500/30 px-1.5 py-0.5 text-[8px] font-bold text-red-300 uppercase">
                  {selectedBase.intensity}
                </span>
              </div>
              <h3 className="mt-1 text-xs font-black text-white">{selectedBase.name}</h3>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-300">
                {selectedBase.details}
              </p>
            </div>
          )}

          {/* Monitored Base Roster List */}
          <div className="mt-4">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Tactical Installations
            </p>
            <div className="space-y-1.5">
              {activeTheater.bases.map((base) => {
                const isSelected = selectedBase?.id === base.id;
                return (
                  <button
                    key={base.id}
                    onClick={() => setSelectedBase(base)}
                    className={`flex w-full items-center justify-between rounded-xl p-2 text-left transition ${
                      isSelected
                        ? "border border-red-500/50 bg-red-500/20 text-white font-bold"
                        : "border border-white/5 bg-white/[0.02] text-slate-300 hover:bg-white/[0.06]"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          base.intensity === "high"
                            ? "bg-red-500"
                            : base.intensity === "medium"
                            ? "bg-amber-400"
                            : "bg-sky-400"
                        }`}
                      />
                      <span className="truncate text-[11px]">{base.name}</span>
                    </div>
                    <span className="font-mono text-[9px] text-slate-400 uppercase shrink-0 ml-2">
                      {base.type}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-white/10 text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>SOURCE: NASA / ESRI / AMTI</span>
            <button
              onClick={() => setShowClassificationModal(true)}
              className="text-blue-400 hover:underline"
            >
              METHODOLOGY →
            </button>
          </div>
        </aside>
      )}

      {/* BOTTOM REAL-TIME NEWS / DISPATCH TICKER (Matches bottom bar in screenshot) */}
      <div className="pointer-events-none absolute bottom-3 left-4 right-4 z-[500] flex items-center justify-between">
        <div className="pointer-events-auto flex flex-1 items-center gap-3 overflow-hidden rounded-xl border border-white/15 bg-[#090e1a]/95 px-3 py-2 text-xs shadow-2xl backdrop-blur-md">
          {/* Red Headline Badge */}
          <div className="flex shrink-0 items-center gap-1.5 rounded-lg bg-red-600 px-2.5 py-1 text-[10px] font-black uppercase tracking-wider text-white shadow-sm">
            <span>{currentNewsTheater.shortName}</span>
          </div>

          {/* Scrolling / Live News Text */}
          <div className="flex items-center gap-2 overflow-hidden truncate">
            <span className="font-mono text-[10px] font-bold text-red-400 uppercase tracking-wider shrink-0">
              {currentNewsTheater.headline.source}
            </span>
            <span className="h-3 w-px bg-white/20 shrink-0" />
            <span className="truncate text-slate-200 font-medium text-[11px]">
              {currentNewsTheater.headline.text}
            </span>
          </div>

          <span className="ml-auto hidden font-mono text-[10px] text-slate-400 sm:inline shrink-0">
            Imagery: NASA / Blue Marble / Esri
          </span>
        </div>
      </div>

      {/* CLASSIFICATION METHODOLOGY MODAL */}
      {showClassificationModal && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl border border-white/15 bg-[#0e1424] p-6 text-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-blue-400">
                Threat Classification Methodology
              </h3>
              <button
                onClick={() => setShowClassificationModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="my-4 space-y-3 text-xs leading-relaxed text-slate-300">
              <p>
                The intelligence tracking platform categorizes geospatial theaters based on real-time multi-source data streams:
              </p>
              <div className="space-y-2 rounded-xl bg-white/5 p-3 font-mono text-[11px]">
                <p>🔴 <strong className="text-red-400">High Intensity:</strong> Active kinetic artillery exchanges, combat sorties, or direct missile interdictions within the last 48 hours.</p>
                <p>🟠 <strong className="text-amber-400">Medium / Elevated:</strong> Fortified base expansion, militarized island reclamation, radar tracking sorties, and heightened standoff postures.</p>
                <p>🟢 <strong className="text-emerald-400">Lower Intensity:</strong> Stabilized ceasefires with baseline observation and electronic reconnaissance.</p>
                <p>🔵 <strong className="text-sky-400">Watch / Flashpoint:</strong> Contested maritime choke points or diplomatic gray-zone sovereign tensions.</p>
              </div>
            </div>

            <button
              onClick={() => setShowClassificationModal(false)}
              className="w-full rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white transition hover:bg-blue-700"
            >
              Close
            </button>
          </div>
        </div>
      )}

    </div>
  );
}