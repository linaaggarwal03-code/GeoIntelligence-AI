"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import * as THREE from "three";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Compass,
  Crosshair,
  ExternalLink,
  Flame,
  Globe2,
  Info,
  Layers,
  MapPin,
  Menu,
  Minus,
  Navigation,
  Pause,
  Play,
  Plus,
  Radio,
  Rotate3D,
  RotateCcw,
  Search,
  Shield,
  ShieldAlert,
  Volume2,
  X,
  Zap,
} from "lucide-react";

export type IntensityLevel = "high" | "medium" | "low" | "watch";

export interface Hotspot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  intensity: IntensityLevel;
  risk: "Critical" | "High" | "Moderate" | "Guarded";
  score: number;
  category: "conflict" | "maritime" | "energy" | "nuclear";
  actor1: string;
  actor2: string;
  summary: string;
  telemetry: string;
  threatLevel: string;
}

// 29 THEATERS EXACTLY MATCHING THE USER'S LIVE GLOBAL THEATERS SCREENSHOT
export const HOTSPOTS: Hotspot[] = [
  // HIGH INTENSITY (🔴 Red)
  {
    id: "ukraine",
    name: "Eastern Europe (Donbas / Black Sea)",
    lat: 48.37,
    lng: 37.8,
    intensity: "high",
    risk: "Critical",
    score: 94,
    category: "conflict",
    actor1: "Ukraine",
    actor2: "Russia",
    summary: "Active frontline combat, high-density drone swarms, and Black Sea maritime reconnaissance.",
    telemetry: "Airspace: Restricted. EW Jamming: Level 4. Frontline kinetic exchanges constant.",
    threatLevel: "Code Red — Kinetic High-Intensity",
  },
  {
    id: "gaza",
    name: "Levant & Gaza Strip (Southern Levant)",
    lat: 31.45,
    lng: 34.4,
    intensity: "high",
    risk: "Critical",
    score: 92,
    category: "conflict",
    actor1: "Israel Defense Forces",
    actor2: "Hamas / Regional Militias",
    summary: "Urban kinetic operations, precision airstrikes, and fortified defensive perimeter interdiction.",
    telemetry: "Air Defenses: Iron Dome / Arrow Active. Border corridor heavily militarized.",
    threatLevel: "Code Red — Multi-Front Kinetic Fire",
  },
  {
    id: "lebanon_border",
    name: "Israel-Lebanon Border (Blue Line)",
    lat: 33.25,
    lng: 35.45,
    intensity: "high",
    risk: "Critical",
    score: 90,
    category: "conflict",
    actor1: "Israel Defense Forces",
    actor2: "Hezbollah",
    summary: "Cross-border rocket and drone volleys, artillery exchanges, and deep reconnaissance sweeps.",
    telemetry: "Northern Air Defense Alert: Max. Displacement corridors established.",
    threatLevel: "Code Red — Rocket & Drone Artillery Zone",
  },
  {
    id: "sudan",
    name: "Sudan Civil War (Khartoum & Darfur)",
    lat: 15.55,
    lng: 32.53,
    intensity: "high",
    risk: "Critical",
    score: 89,
    category: "conflict",
    actor1: "Sudanese Armed Forces (SAF)",
    actor2: "Rapid Support Forces (RSF)",
    summary: "Severe urban fighting in capital hub and mass displacement along western desert corridors.",
    telemetry: "Humanitarian access severed; Red Sea logistics staging at Port Sudan.",
    threatLevel: "Code Red — Systemic Kinetic War",
  },
  {
    id: "myanmar",
    name: "Myanmar Civil War (Shan & Sagaing)",
    lat: 21.91,
    lng: 96.08,
    intensity: "high",
    risk: "Critical",
    score: 87,
    category: "conflict",
    actor1: "Military Junta (SAC)",
    actor2: "Three Brotherhood Alliance / PDF",
    summary: "Ethnic resistance offensives, junta airstrikes, and border trade corridor seizures.",
    telemetry: "Border crossings closed; rare-earth and tin logistical chokepoints contested.",
    threatLevel: "Code Red — Multi-Front Guerrilla Warfare",
  },
  {
    id: "drc_kivu",
    name: "Eastern DRC (North Kivu & Goma)",
    lat: -1.68,
    lng: 29.22,
    intensity: "high",
    risk: "Critical",
    score: 86,
    category: "conflict",
    actor1: "FARDC & SADC Troops",
    actor2: "M23 Rebels / Armed Groups",
    summary: "Heavy artillery around Goma perimeter, coltan and cobalt mineral supply belt insecurity.",
    telemetry: "Critical mineral logistics corridors disrupted; drone surveillance active.",
    threatLevel: "Code Red — Strategic Mineral Corridor Conflict",
  },
  {
    id: "sahel_mali",
    name: "Central Sahel (Mali, Burkina Faso & Niger)",
    lat: 14.5,
    lng: -1.2,
    intensity: "high",
    risk: "Critical",
    score: 85,
    category: "conflict",
    actor1: "Alliance of Sahel States (AES)",
    actor2: "JNIM & Islamic State in Sahel",
    summary: "Uranium supply hub volatility, convoy ambushes, and mercenary forward defense footprints.",
    telemetry: "Border patrols mobilized; mining logistical access restricted.",
    threatLevel: "Code Red — Asymmetric Insurgent Pressure",
  },

  // MEDIUM / ELEVATED (🟠 Orange)
  {
    id: "red_sea",
    name: "Southern Red Sea & Bab-el-Mandeb",
    lat: 12.8,
    lng: 43.3,
    intensity: "medium",
    risk: "High",
    score: 84,
    category: "maritime",
    actor1: "Houthi Forces",
    actor2: "Commercial Fleet & Naval Coalition",
    summary: "Anti-ship ballistic missile and drone boat interdiction against Suez shipping transit.",
    telemetry: "Container Transit: -58% YoY. Cape of Good Hope rerouting persistent.",
    threatLevel: "Code Amber — Maritime Chokepoint Interdiction",
  },
  {
    id: "somalia",
    name: "Somalia & Horn of Africa (Mogadishu)",
    lat: 2.04,
    lng: 45.34,
    intensity: "medium",
    risk: "High",
    score: 78,
    category: "conflict",
    actor1: "Somali Federal Army & ATMIS",
    actor2: "Al-Shabaab",
    summary: "Sustained counter-insurgency offensive and maritime piracy surveillance off Puntland.",
    telemetry: "Naval patrols monitoring Gulf of Aden transit corridors.",
    threatLevel: "Code Amber — Coastal & Insurgent Threat",
  },
  {
    id: "syria",
    name: "Northern Syria (Idlib & Euphrates)",
    lat: 35.95,
    lng: 38.9,
    intensity: "medium",
    risk: "High",
    score: 77,
    category: "conflict",
    actor1: "Syrian Armed Forces & Allies",
    actor2: "SDF & Opposition Factions",
    summary: "Artillery duels, cross-border Turkish drone strikes, and counter-terror raids.",
    telemetry: "Airspace partitioned into de-confliction corridors.",
    threatLevel: "Code Amber — Partitioned Territorial Standoff",
  },
  {
    id: "lake_chad",
    name: "Lake Chad Basin (Borno / Cameroon)",
    lat: 13.0,
    lng: 14.1,
    intensity: "medium",
    risk: "High",
    score: 75,
    category: "conflict",
    actor1: "Multinational Joint Task Force",
    actor2: "ISWAP / Boko Haram",
    summary: "Counter-insurgency operations around island hideouts and border trade networks.",
    telemetry: "Border security arrays deployed across Lake Chad perimeter.",
    threatLevel: "Code Amber — Asymmetric Border Raid Risk",
  },
  {
    id: "colombia",
    name: "Colombia (Catatumbo & Cauca)",
    lat: 8.25,
    lng: -73.35,
    intensity: "medium",
    risk: "High",
    score: 74,
    category: "conflict",
    actor1: "Colombian Military",
    actor2: "ELN & FARC Dissident Factions",
    summary: "Clashes over illicit coca corridors and border crossing infrastructure.",
    telemetry: "Riverine military interdiction ongoing.",
    threatLevel: "Code Amber — Drug Corridor Guerrilla Clashes",
  },
  {
    id: "pak_afghan",
    name: "Pakistan-Afghanistan Border (Khyber)",
    lat: 33.9,
    lng: 70.8,
    intensity: "medium",
    risk: "High",
    score: 73,
    category: "conflict",
    actor1: "Pakistan Security Forces",
    actor2: "TTP / Afghan Frontier Forces",
    summary: "Border post skirmishes, cross-border shelling, and TTP ambush operations.",
    telemetry: "Durand Line sensor fences under reinforced watch.",
    threatLevel: "Code Amber — Frontier Border Tension",
  },
  {
    id: "haiti",
    name: "Haiti (Port-au-Prince Metropolitan)",
    lat: 18.54,
    lng: -72.34,
    intensity: "medium",
    risk: "High",
    score: 72,
    category: "conflict",
    actor1: "Haitian Police & MSS Mission",
    actor2: "Viv Ansanm Gang Coalition",
    summary: "Port and airport security operations against criminal cartel encirclement.",
    telemetry: "Maritime approaches patrolled by multinational coast guards.",
    threatLevel: "Code Amber — Critical Urban Asset Vulnerability",
  },
  {
    id: "mexico",
    name: "Northern Mexico (Sinaloa Corridor)",
    lat: 24.8,
    lng: -107.4,
    intensity: "medium",
    risk: "High",
    score: 71,
    category: "conflict",
    actor1: "Mexican Armed Forces / Guard",
    actor2: "Cartel Factions (Los Chapitos)",
    summary: "Heavy vehicular blockades, armed drone skirmishes, and fentanyl supply interdiction.",
    telemetry: "Helicopter surveillance and highway checkpoints active.",
    threatLevel: "Code Amber — Heavy Cartel Kinetic Clashes",
  },

  // LOWER INTENSITY (🟢 Green)
  {
    id: "mozambique",
    name: "Northern Mozambique (Cabo Delgado)",
    lat: -12.97,
    lng: 40.51,
    intensity: "low",
    risk: "Moderate",
    score: 65,
    category: "energy",
    actor1: "Mozambique & Rwandan Forces",
    actor2: "Al-Sunnah wa Jama'ah",
    summary: "Protection patrols guarding TotalEnergies and ExxonMobil offshore LNG facilities.",
    telemetry: "LNG offshore extraction perimeter secured by naval craft.",
    threatLevel: "Code Green — Offshore Energy Perimeter Guard",
  },
  {
    id: "car",
    name: "Central African Republic (Bambari)",
    lat: 5.76,
    lng: 20.68,
    intensity: "low",
    risk: "Moderate",
    score: 63,
    category: "conflict",
    actor1: "FACA & Bilateral Security Forces",
    actor2: "CPC Coalition Rebels",
    summary: "Diamond and gold artisanal mining corridors protected by roving patrols.",
    telemetry: "UN peacekeeping peace monitoring checkpoints active.",
    threatLevel: "Code Green — Resource Route Patrols",
  },
  {
    id: "ethiopia",
    name: "Ethiopia (Amhara & Oromia)",
    lat: 11.5,
    lng: 37.5,
    intensity: "low",
    risk: "Moderate",
    score: 62,
    category: "conflict",
    actor1: "ENDF Federal Forces",
    actor2: "Fano Militia / OLA",
    summary: "State of emergency operations, road transit checkpoints, and regional disarmament.",
    telemetry: "Main highway from Addis Ababa to Bahir Dar guarded.",
    threatLevel: "Code Green — Internal Security Checkpoints",
  },
  {
    id: "libya",
    name: "Libya (Sirte-Jufra Oil Crescent)",
    lat: 30.08,
    lng: 17.58,
    intensity: "low",
    risk: "Moderate",
    score: 59,
    category: "energy",
    actor1: "GNU Forces (Tripoli)",
    actor2: "LNA (Tobruk / Haftar)",
    summary: "Divided governance over Mediterranean oil export terminals (Ras Lanuf / Es Sider).",
    telemetry: "Crude loading terminals operating under monitored ceasefire.",
    threatLevel: "Code Green — Hydrocarbon Chokepoint Equilibrium",
  },
  {
    id: "armenia_az",
    name: "Armenia-Azerbaijan (Syunik Corridor)",
    lat: 39.5,
    lng: 46.5,
    intensity: "low",
    risk: "Moderate",
    score: 58,
    category: "conflict",
    actor1: "Armenian Armed Forces",
    actor2: "Azerbaijani Armed Forces",
    summary: "Border delimitation talks ongoing; sporadic border sniper exchanges.",
    telemetry: "EU civilian monitoring mission (EUMA) patrols along Syunik border.",
    threatLevel: "Code Green — Fragile Border Peace Talks",
  },
  {
    id: "philippines_south",
    name: "Southern Philippines (Sulu & Mindanao)",
    lat: 6.05,
    lng: 121.0,
    intensity: "low",
    risk: "Moderate",
    score: 55,
    category: "maritime",
    actor1: "Philippine Armed Forces",
    actor2: "BIFF / Abu Sayyaf Splinters",
    summary: "Maritime interdiction of smuggling routes through Sulu and Celebes Seas.",
    telemetry: "Trilateral naval patrols with Malaysia and Indonesia.",
    threatLevel: "Code Green — Maritime Counter-Smuggling",
  },
  {
    id: "western_sahara",
    name: "Western Sahara (Berm Buffer Zone)",
    lat: 24.2,
    lng: -12.9,
    intensity: "low",
    risk: "Moderate",
    score: 52,
    category: "conflict",
    actor1: "Royal Moroccan Armed Forces",
    actor2: "Polisario Front",
    summary: "Long-range harassment artillery across sand berm wall; drone observation.",
    telemetry: "MINURSO observer posts stationed along separation line.",
    threatLevel: "Code Green — Low-Intensity Desert Wall Standoff",
  },

  // WATCH / FLASHPOINT (🔵 Blue)
  {
    id: "taiwan_strait",
    name: "Taiwan Strait & ADIZ Corridor",
    lat: 24.0,
    lng: 120.5,
    intensity: "watch",
    risk: "High",
    score: 81,
    category: "conflict",
    actor1: "Taiwan / US Allied Fleets",
    actor2: "China (PLA Eastern Theater)",
    summary: "Median line sorties, carrier strike group maneuvers, and microchip logistics choke.",
    telemetry: "ADIZ Incursions: 28 sorties / 48h. Anti-submarine naval sweeps monitored.",
    threatLevel: "Code Blue — Air-Sea Standoff Flashpoint",
  },
  {
    id: "south_china_sea",
    name: "South China Sea (Spratly Islands)",
    lat: 10.0,
    lng: 114.0,
    intensity: "watch",
    risk: "High",
    score: 80,
    category: "maritime",
    actor1: "Philippines / US Partners",
    actor2: "China Coast Guard & Maritime Militia",
    summary: "Water cannon encounters at Second Thomas Shoal, Sabina Shoal, and Scarborough Reef.",
    telemetry: "Submarine transit channels monitored; maritime militia vessels deployed.",
    threatLevel: "Code Blue — Maritime Sovereignty Flashpoint",
  },
  {
    id: "korean_peninsula",
    name: "Korean Peninsula (38th Parallel & DMZ)",
    lat: 38.32,
    lng: 127.1,
    intensity: "watch",
    risk: "High",
    score: 79,
    category: "nuclear",
    actor1: "South Korea / US Combined Forces",
    actor2: "North Korea (KPA)",
    summary: "Hypersonic missile testing, fortified border walls, and spy satellite launches.",
    telemetry: "Satellite Recon: TEL deployment logged near Sunan air base.",
    threatLevel: "Code Blue — Ballistic Posture Flashpoint",
  },
  {
    id: "india_china_lac",
    name: "India-China LAC (Ladakh & Arunachal)",
    lat: 34.15,
    lng: 77.57,
    intensity: "watch",
    risk: "Moderate",
    score: 69,
    category: "conflict",
    actor1: "Indian Army",
    actor2: "PLA Western Theater Command",
    summary: "High-altitude winterized bunkers, disengagement patrols, and road infrastructure build.",
    telemetry: "Thermal UAV patrols active along Galwan and Depsang plains.",
    threatLevel: "Code Blue — Mountain Border Guarded Watch",
  },
  {
    id: "hormuz",
    name: "Strait of Hormuz (Persian Gulf)",
    lat: 26.56,
    lng: 56.25,
    intensity: "watch",
    risk: "Critical",
    score: 88,
    category: "maritime",
    actor1: "US Naval Forces & Allies",
    actor2: "IRGC Navy",
    summary: "Vessel tracking for 21 million barrels/day of global crude flow; naval boarding drills.",
    telemetry: "GPS spoofing logged near Qeshm Island; fast-attack missile craft monitored.",
    threatLevel: "Code Blue — Energy Chokepoint Flashpoint",
  },
  {
    id: "suwalki_gap",
    name: "Suwalki Gap & Baltic Sea",
    lat: 54.3,
    lng: 23.3,
    intensity: "watch",
    risk: "Moderate",
    score: 67,
    category: "conflict",
    actor1: "NATO Baltic Battlegroups",
    actor2: "Russia (Kaliningrad) / Belarus",
    summary: "Corridor separating Kaliningrad from Belarus; electronic jamming over Baltic airspace.",
    telemetry: "GPS jamming logged affecting commercial flights across Baltic corridor.",
    threatLevel: "Code Blue — NATO Frontier Chokepoint",
  },
  {
    id: "guyana_essequibo",
    name: "Guyana-Venezuela Border (Essequibo)",
    lat: 6.8,
    lng: -59.5,
    intensity: "watch",
    risk: "Moderate",
    score: 61,
    category: "energy",
    actor1: "Guyana Defense Force",
    actor2: "Venezuela Bolivarian Armed Forces",
    summary: "Offshore oil blocks (Stabroek) contested; military staging on Ankoko Island.",
    telemetry: "Joint aerial patrols with US Southern Command ongoing.",
    threatLevel: "Code Blue — Offshore Hydrocarbon Dispute",
  },
  {
    id: "arctic_barents",
    name: "Arctic (Barents Sea Chokepoint)",
    lat: 71.0,
    lng: 28.0,
    intensity: "watch",
    risk: "Moderate",
    score: 57,
    category: "maritime",
    actor1: "NATO Northern Fleet (Norway/US)",
    actor2: "Russian Northern Fleet (Kola)",
    summary: "Nuclear ballistic submarine transit patrols through GIUK-N gap and Northern Sea Route.",
    telemetry: "Underwater acoustic hydrophone array listening post operational.",
    threatLevel: "Code Blue — Strategic Nuclear Submarine Watch",
  },
];

export const LIVE_NEWS_DISPATCHES = [
  { source: "INFORMED COMMENT", text: "The Taliban Wants US Recognition. What Do Afghans Want?" },
  { source: "CNN", text: "Trump backed Iran into a corner. The regime is expanding its naval and missile posturing." },
  { source: "REUTERS", text: "Sudan ceasefire negotiations stall in Jeddah as artillery exchanges rock Khartoum." },
  { source: "AL JAZEERA", text: "Red Sea coalition monitors intensified drone boat deployments near Hodeidah approaches." },
  { source: "BBC", text: "Myanmar resistance fighters expand control over strategic jade and rare earth transit corridors." },
  { source: "FINANCIAL TIMES", text: "Oil tankers reroute around Cape of Good Hope, sustaining elevated marine insurance rates." },
];

function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

// Generates an equirectangular photorealistic earth texture on HTML Canvas
function createEarthCanvas(): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d")!;

  // 1. Ocean gradient base
  const oceanGrad = ctx.createLinearGradient(0, 0, 0, 1024);
  oceanGrad.addColorStop(0, "#08214d");
  oceanGrad.addColorStop(0.5, "#061329");
  oceanGrad.addColorStop(1, "#08214d");
  ctx.fillStyle = oceanGrad;
  ctx.fillRect(0, 0, 2048, 1024);

  const mapPt = (lat: number, lng: number): [number, number] => {
    const x = ((lng + 180) / 360) * 2048;
    const y = ((90 - lat) / 180) * 1024;
    return [x, y];
  };

  const drawCont = (pts: [number, number][], fill: string, stroke?: string) => {
    if (pts.length === 0) return;
    ctx.beginPath();
    const [sx, sy] = mapPt(pts[0][0], pts[0][1]);
    ctx.moveTo(sx, sy);
    for (let i = 1; i < pts.length; i++) {
      const [px, py] = mapPt(pts[i][0], pts[i][1]);
      ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
  };

  // Africa (South Green, Sahara Gold)
  drawCont([
    [15, -17], [10, -14], [5, 0], [4, 9], [-5, 12], [-15, 12],
    [-25, 15], [-34, 18], [-34, 26], [-28, 32], [-20, 35],
    [-10, 40], [0, 42], [11, 51], [12, 44], [15, 40], [15, -17]
  ], "#22542a", "#17381b");

  drawCont([
    [36, -5], [37, 10], [31, 32], [22, 38], [15, 40], [15, -17],
    [21, -17], [28, -13], [36, -5]
  ], "#c29b63", "#a8824b");

  // Europe & Mediterranean
  drawCont([
    [36, -9], [43, -9], [48, -4], [50, 2], [54, 8], [58, 6],
    [62, 5], [71, 28], [68, 45], [55, 38], [45, 36], [40, 26],
    [38, 22], [42, 14], [36, -5], [36, -9]
  ], "#2d6333", "#1b3a1a");

  // Arabia (Desert)
  drawCont([
    [32, 35], [30, 32], [27, 34], [15, 42], [12, 45], [14, 53],
    [22, 59], [26, 56], [30, 48], [37, 36], [32, 35]
  ], "#b89058", "#99733e");

  // Asia / Eurasia
  drawCont([
    [55, 38], [68, 45], [72, 70], [75, 105], [72, 140], [66, 170],
    [58, 162], [48, 142], [38, 120], [30, 122], [22, 114], [20, 107],
    [10, 105], [1, 104], [6, 100], [15, 96], [22, 90], [10, 77],
    [24, 68], [30, 60], [38, 46], [45, 36], [55, 38]
  ], "#2f6b36", "#1c4021");

  // India
  drawCont([
    [28, 68], [24, 69], [15, 74], [8, 77], [13, 80], [20, 85],
    [22, 88], [28, 80], [28, 68]
  ], "#3b7d42", "#244d28");

  // North America
  drawCont([
    [70, -165], [70, -130], [60, -90], [52, -56], [44, -65], [30, -81],
    [25, -80], [29, -89], [25, -97], [18, -95], [14, -86], [9, -79],
    [16, -93], [23, -106], [32, -117], [48, -125], [58, -136], [65, -168], [70, -165]
  ], "#2d6333", "#1b3a1a");

  // South America
  drawCont([
    [12, -72], [10, -62], [6, -52], [-3, -38], [-8, -35], [-23, -42],
    [-35, -55], [-45, -65], [-55, -68], [-50, -74], [-38, -73], [-20, -70],
    [-4, -80], [8, -77], [12, -72]
  ], "#25572b", "#17381b");

  // Australia
  drawCont([
    [-14, 129], [-11, 142], [-23, 151], [-37, 150], [-38, 140],
    [-32, 116], [-22, 114], [-14, 129]
  ], "#9e7740", "#7a5a2d");

  // Greenland (Ice white)
  drawCont([
    [82, -30], [76, -18], [60, -44], [68, -52], [78, -68], [82, -30]
  ], "#e2e8f0", "#cbd5e1");

  // Antarctica
  ctx.fillStyle = "#e2e8f0";
  ctx.fillRect(0, 890, 2048, 134);

  // Faint Graticule lines over oceans
  ctx.strokeStyle = "rgba(56, 189, 248, 0.16)";
  ctx.lineWidth = 1;
  for (let x = 0; x <= 2048; x += 2048 / 24) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 1024);
    ctx.stroke();
  }
  for (let y = 0; y <= 1024; y += 1024 / 12) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(2048, y);
    ctx.stroke();
  }

  return canvas;
}

interface GlobeView3DProps {
  onSelectHotspot?: (h: Hotspot) => void;
  onSwitchTo2D?: () => void;
}

export default function GlobeView3D({ onSelectHotspot, onSwitchTo2D }: GlobeView3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot>(HOTSPOTS[0]);
  const [showDrawer, setShowDrawer] = useState(false);
  const [showClassificationModal, setShowClassificationModal] = useState(false);
  const [telemetry, setTelemetry] = useState({
    lat: 36.98,
    latDir: "N",
    lng: 19.24,
    lngDir: "E",
    altKm: 12615,
  });

  const onSelectHotspotRef = useRef(onSelectHotspot);
  useEffect(() => {
    onSelectHotspotRef.current = onSelectHotspot;
  }, [onSelectHotspot]);

  // Ticker cycle
  const [tickerIndex, setTickerIndex] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % LIVE_NEWS_DISPATCHES.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const currentNews = LIVE_NEWS_DISPATCHES[tickerIndex];

  // 3D Orbital & Auto-Rotate Controls
  const [isAutoRotating, setIsAutoRotating] = useState(false);
  const autoRotateRef = useRef(false);
  const [tiltPreset, setTiltPreset] = useState<"tactical" | "overhead" | "horizon">("tactical");

  const orbitControlsRef = useRef<{
    zoomIn: () => void;
    zoomOut: () => void;
    resetView: () => void;
    cycleTilt: () => void;
    toggleAutoRotate: () => void;
    flyTo: (lat: number, lng: number) => void;
    goToRegion: (region: "europe" | "asia" | "americas") => void;
  }>({
    zoomIn: () => {},
    zoomOut: () => {},
    resetView: () => {},
    cycleTilt: () => {},
    toggleAutoRotate: () => {},
    flyTo: () => {},
    goToRegion: () => {},
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const getDim = () => {
      const w = container.clientWidth || container.parentElement?.clientWidth || window.innerWidth || 1200;
      const h = Math.max(container.clientHeight || container.parentElement?.clientHeight || 0, 720);
      return { w, h };
    };

    const { w: initW, h: initH } = getDim();

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x040711);

    const camera = new THREE.PerspectiveCamera(45, initW / initH, 0.1, 1000);
    camera.position.set(0, 5, 23);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(initW, initH);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    renderer.domElement.style.position = "absolute";
    renderer.domElement.style.top = "0";
    renderer.domElement.style.left = "0";

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const GLOBE_RADIUS = 8.0;
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);
    globeGroup.rotation.set(0, 0, 0);

    // 1. Earth Sphere
    const earthCanvas = createEarthCanvas();
    const canvasTexture = new THREE.CanvasTexture(earthCanvas);
    canvasTexture.colorSpace = THREE.SRGBColorSpace;
    canvasTexture.needsUpdate = true;

    const globeGeo = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const globeMat = new THREE.MeshPhongMaterial({
      map: canvasTexture,
      specular: new THREE.Color(0x1a365d),
      shininess: 18,
    });
    const globeMesh = new THREE.Mesh(globeGeo, globeMat);
    globeGroup.add(globeMesh);

    // Progressive texture loading from CDN
    const textureLoader = new THREE.TextureLoader();
    textureLoader.setCrossOrigin("anonymous");
    textureLoader.load(
      "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg",
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        globeMat.map = tex;
        globeMat.needsUpdate = true;
      },
      undefined,
      () => {}
    );

    // 2. Graticule Wireframe Sphere
    const gridGeo = new THREE.SphereGeometry(GLOBE_RADIUS * 1.002, 36, 18);
    const gridMat = new THREE.MeshBasicMaterial({
      color: 0x1e3a8a,
      wireframe: true,
      transparent: true,
      opacity: 0.16,
    });
    globeGroup.add(new THREE.Mesh(gridGeo, gridMat));

    // 3. Reliable Atmospheric Halo (Using clean standard Three.js material)
    const atmoGeo = new THREE.SphereGeometry(GLOBE_RADIUS * 1.08, 48, 48);
    const atmoMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.12,
      side: THREE.BackSide,
    });
    globeGroup.add(new THREE.Mesh(atmoGeo, atmoMat));

    // 4. Background Starfield
    const starsGeo = new THREE.BufferGeometry();
    const starCount = 600;
    const starCoords = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starCoords[i] = (Math.random() - 0.5) * 160;
      starCoords[i + 1] = (Math.random() - 0.5) * 160;
      starCoords[i + 2] = (Math.random() - 0.5) * 160;
    }
    starsGeo.setAttribute("position", new THREE.BufferAttribute(starCoords, 3));
    const starsMat = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.5,
      transparent: true,
      opacity: 0.35,
    });
    const starField = new THREE.Points(starsGeo, starsMat);
    scene.add(starField);

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.5);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 2.0);
    sunLight.position.set(15, 12, 18);
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    fillLight.position.set(-18, -10, -15);
    scene.add(fillLight);

    // 6. 3D Extruded Pill Columns for all 29 Theaters
    const clickableObjects: THREE.Object3D[] = [];
    const pulsingRings: { mesh: THREE.Mesh }[] = [];

    HOTSPOTS.forEach((h) => {
      const markerGroup = new THREE.Group();
      const pos = latLngToVector3(h.lat, h.lng, GLOBE_RADIUS);
      markerGroup.position.copy(pos);

      const normal = pos.clone().normalize();
      markerGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);

      let colorHex = 0x38bdf8;
      let height = 0.9;
      let radius = 0.16;

      if (h.intensity === "high") {
        colorHex = 0xef4444;
        height = 2.4;
        radius = 0.22;
      } else if (h.intensity === "medium") {
        colorHex = 0xf97316;
        height = 1.7;
        radius = 0.19;
      } else if (h.intensity === "low") {
        colorHex = 0x22c55e;
        height = 1.1;
        radius = 0.17;
      }

      // Column cylinder
      const cylGeo = new THREE.CylinderGeometry(radius, radius, height, 16);
      cylGeo.translate(0, height / 2, 0);

      const cylMat = new THREE.MeshPhongMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.7,
        shininess: 60,
      });

      const cylMesh = new THREE.Mesh(cylGeo, cylMat);
      cylMesh.userData = { hotspot: h };
      markerGroup.add(cylMesh);
      clickableObjects.push(cylMesh);

      // Glowing top cap
      const capGeo = new THREE.SphereGeometry(radius * 1.05, 12, 12);
      capGeo.translate(0, height, 0);
      const capMesh = new THREE.Mesh(capGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }));
      markerGroup.add(capMesh);

      // Ground concentric radar rings for High intensity zones
      if (h.intensity === "high") {
        for (let r = 1; r <= 3; r++) {
          const ringGeo = new THREE.RingGeometry(0.35 * r, 0.42 * r, 32);
          ringGeo.rotateX(-Math.PI / 2);
          const ringMat = new THREE.MeshBasicMaterial({
            color: 0xef4444,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.55 / r,
          });
          const ringMesh = new THREE.Mesh(ringGeo, ringMat);
          ringMesh.position.y = 0.04;
          markerGroup.add(ringMesh);
          pulsingRings.push({ mesh: ringMesh });
        }
      }

      globeGroup.add(markerGroup);
    });

    // 3D Orbital Spherical Coordinates
    // Phi: Polar angle (pitch/elevation). 0 is North Pole (+Y), PI is South Pole (-Y).
    // Theta: Azimuth (horizontal yaw spin). 360 continuous rotation.
    // Radius: Distance from globe center (zoom).
    let currentPhi = (90 - 28) * (Math.PI / 180); // ~28° N initial view
    let currentTheta = (25 + 180) * (Math.PI / 180); // ~25° E initial view
    let currentRadius = 23.0;

    let targetPhi = currentPhi;
    let targetTheta = currentTheta;
    let targetRadius = currentRadius;

    let velocityTheta = 0;
    let velocityPhi = 0;

    const updateCameraPosition = () => {
      const x = -(currentRadius * Math.sin(currentPhi) * Math.cos(currentTheta));
      const y = currentRadius * Math.cos(currentPhi);
      const z = currentRadius * Math.sin(currentPhi) * Math.sin(currentTheta);
      camera.position.set(x, y, z);
      camera.lookAt(0, 0, 0);
      camera.up.set(0, 1, 0);
    };
    updateCameraPosition();

    // Telemetry updater
    const syncTelemetry = () => {
      const latVal = 90 - (currentPhi * 180) / Math.PI;
      const lngVal = (((currentTheta * 180) / Math.PI - 180) % 360 + 540) % 360 - 180;
      const altitudeKm = Math.round(currentRadius * 548);

      setTelemetry({
        lat: Math.abs(parseFloat(latVal.toFixed(2))),
        latDir: latVal >= 0 ? "N" : "S",
        lng: Math.abs(parseFloat(lngVal.toFixed(2))),
        lngDir: lngVal >= 0 ? "E" : "W",
        altKm: altitudeKm,
      });
    };

    orbitControlsRef.current = {
      zoomIn: () => {
        targetRadius = Math.max(11.5, targetRadius - 2.5);
      },
      zoomOut: () => {
        targetRadius = Math.min(38.0, targetRadius + 2.5);
      },
      resetView: () => {
        targetPhi = (90 - 28) * (Math.PI / 180);
        targetTheta = (25 + 180) * (Math.PI / 180);
        targetRadius = 23.0;
        velocityTheta = 0;
        velocityPhi = 0;
      },
      cycleTilt: () => {
        setTiltPreset((prev) => {
          if (prev === "tactical") {
            targetPhi = 0.28; // ~74° High-altitude top-down perspective
            return "overhead";
          } else if (prev === "overhead") {
            targetPhi = 1.45; // ~7° Horizon view
            return "horizon";
          } else {
            targetPhi = 0.85; // ~41° Tactical 3D Orbit
            return "tactical";
          }
        });
      },
      toggleAutoRotate: () => {
        setIsAutoRotating((prev) => {
          const next = !prev;
          autoRotateRef.current = next;
          return next;
        });
      },
      flyTo: (lat: number, lng: number) => {
        targetPhi = Math.max(0.06, Math.min(Math.PI - 0.06, (90 - lat) * (Math.PI / 180)));
        targetTheta = (lng + 180) * (Math.PI / 180);
        targetRadius = 15.5;
        velocityTheta = 0;
        velocityPhi = 0;
      },
      goToRegion: (region: "europe" | "asia" | "americas") => {
        if (region === "europe") {
          targetPhi = (90 - 32) * (Math.PI / 180);
          targetTheta = (35 + 180) * (Math.PI / 180);
          targetRadius = 20.0;
        } else if (region === "asia") {
          targetPhi = (90 - 24) * (Math.PI / 180);
          targetTheta = (105 + 180) * (Math.PI / 180);
          targetRadius = 20.0;
        } else {
          targetPhi = (90 - 15) * (Math.PI / 180);
          targetTheta = (-75 + 180) * (Math.PI / 180);
          targetRadius = 20.0;
        }
        velocityTheta = 0;
        velocityPhi = 0;
      },
    };

    // Pointer events with pointer capture for buttery smooth 3D orbit
    let isDragging = false;
    let dragDistance = 0;
    let prevPointerX = 0;
    let prevPointerY = 0;

    const onPointerDown = (e: PointerEvent) => {
      dom.setPointerCapture(e.pointerId);
      isDragging = true;
      dragDistance = 0;
      prevPointerX = e.clientX;
      prevPointerY = e.clientY;
      velocityTheta = 0;
      velocityPhi = 0;
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevPointerX;
      const deltaY = e.clientY - prevPointerY;
      dragDistance += Math.abs(deltaX) + Math.abs(deltaY);

      // Rotating view: moving right pulls globe right -> camera angle decreases
      targetTheta -= deltaX * 0.0055;
      targetPhi -= deltaY * 0.0055;
      targetPhi = Math.max(0.06, Math.min(Math.PI - 0.06, targetPhi));

      velocityTheta = -deltaX * 0.0016;
      velocityPhi = -deltaY * 0.0016;

      prevPointerX = e.clientX;
      prevPointerY = e.clientY;
    };

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onPointerUp = (e: PointerEvent) => {
      if (dom.hasPointerCapture(e.pointerId)) {
        dom.releasePointerCapture(e.pointerId);
      }
      isDragging = false;

      // If minimal drag occurred (< 6px), treat as hotspot click
      if (dragDistance < 6) {
        const rect = dom.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(clickableObjects);

        if (intersects.length > 0) {
          const targetObj = intersects[0].object;
          const hotspot = targetObj.userData.hotspot as Hotspot;
          if (hotspot) {
            setSelectedHotspot(hotspot);
            if (onSelectHotspotRef.current) onSelectHotspotRef.current(hotspot);

            targetPhi = Math.max(0.06, Math.min(Math.PI - 0.06, (90 - hotspot.lat) * (Math.PI / 180)));
            targetTheta = (hotspot.lng + 180) * (Math.PI / 180);
            targetRadius = 15.5;
            velocityTheta = 0;
            velocityPhi = 0;
          }
        }
      }
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      targetRadius += e.deltaY * 0.016;
      targetRadius = Math.max(11.5, Math.min(38.0, targetRadius));
    };

    const dom = renderer.domElement;
    dom.style.touchAction = "none";
    dom.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    dom.addEventListener("wheel", onWheel, { passive: false });

    // Animation Loop
    let animationFrameId: number;
    let startTime = performance.now();
    let lastTelemetrySync = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const now = performance.now();
      const elapsed = (now - startTime) / 1000;

      // Pulsing rings animation
      pulsingRings.forEach((ring, idx) => {
        const pulse = 1 + (Math.sin(elapsed * 2.5 + idx * 0.5) + 1) * 0.15;
        ring.mesh.scale.set(pulse, pulse, 1);
      });

      starField.rotation.y += 0.0001;

      // Auto rotation
      if (autoRotateRef.current && !isDragging) {
        targetTheta += 0.0012;
      }

      // Momentum inertia damping
      if (!isDragging) {
        targetTheta += velocityTheta;
        targetPhi += velocityPhi;
        velocityTheta *= 0.90;
        velocityPhi *= 0.90;
      }

      targetPhi = Math.max(0.06, Math.min(Math.PI - 0.06, targetPhi));
      targetRadius = Math.max(11.5, Math.min(38.0, targetRadius));

      // Smooth camera interpolation
      currentPhi += (targetPhi - currentPhi) * 0.11;
      currentTheta += (targetTheta - currentTheta) * 0.11;
      currentRadius += (targetRadius - currentRadius) * 0.11;

      updateCameraPosition();

      // Telemetry sync throttled to 10Hz
      if (now - lastTelemetrySync > 100) {
        lastTelemetrySync = now;
        syncTelemetry();
      }

      renderer.render(scene, camera);
    };

    animate();
    syncTelemetry();

    const handleResize = () => {
      if (!container) return;
      const { w, h } = getDim();
      if (w > 0 && h > 0) {
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      }
    };

    window.addEventListener("resize", handleResize);
    const ro = new ResizeObserver(() => handleResize());
    ro.observe(container);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      ro.disconnect();
      dom.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      dom.removeEventListener("wheel", onWheel);
      renderer.dispose();
    };
  }, []);

  const handleSelectDrawerTheater = (h: Hotspot) => {
    setSelectedHotspot(h);
    if (onSelectHotspotRef.current) onSelectHotspotRef.current(h);
    orbitControlsRef.current.flyTo(h.lat, h.lng);
    setShowDrawer(false);
  };

  return (
    <div
      style={{ width: "100%", height: "100%", minHeight: "720px", position: "relative" }}
      className="relative h-full w-full select-none overflow-hidden rounded-2xl bg-[#040711] font-sans"
    >
      {/* 3D WebGL Canvas Viewport */}
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%", minHeight: "720px", position: "relative" }}
        className="h-full w-full cursor-grab active:cursor-grabbing"
      />

      {/* TOP HEADER: UPDATED DATE & SOURCES */}
      <div className="pointer-events-none absolute left-6 top-3 z-10 flex items-center gap-8 text-[11px] font-mono tracking-wider">
        <div>
          <span className="block text-[9px] font-bold text-slate-500 uppercase">Updated</span>
          <span className="font-semibold text-slate-200">2026-10-06</span>
        </div>
        <div>
          <span className="block text-[9px] font-bold text-slate-500 uppercase">Sources</span>
          <span className="font-semibold text-slate-300">UCDP · ACLED · CFR</span>
        </div>
      </div>

      {/* TOP HUD BAR: Menu [≡], 🔴 LIVE Status Pill, & Telemetry Coordinates */}
      <div className="pointer-events-none absolute left-6 right-6 top-11 z-20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDrawer(!showDrawer)}
            className="pointer-events-auto flex h-9 w-9 items-center justify-center rounded-lg border border-white/20 bg-[#0a0f1d]/90 text-white shadow-2xl backdrop-blur-md transition hover:bg-white/10"
            title="Theaters Directory"
          >
            <Menu className="h-4 w-4" />
          </button>

          <div className="pointer-events-auto flex items-center gap-2 rounded-lg border border-white/15 bg-[#0a0f1d]/85 px-3 py-1.5 shadow-xl backdrop-blur-md">
            <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
            <span className="font-mono text-[10px] font-bold tracking-wider text-slate-200 uppercase">
              LIVE · 29 Theaters · Updated 2026-10-06
            </span>
          </div>
        </div>

        {/* Right Telemetry Coordinates Pill */}
        <div className="flex items-center gap-2">
          {onSwitchTo2D && (
            <button
              onClick={onSwitchTo2D}
              className="pointer-events-auto flex items-center gap-1.5 rounded-lg border border-white/20 bg-[#0a0f1d]/85 px-3 py-1.5 font-mono text-[11px] font-semibold text-blue-400 hover:text-white transition backdrop-blur-md"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>2D Satellite</span>
            </button>
          )}

          <div className="pointer-events-auto flex items-center gap-3 rounded-lg border border-white/15 bg-[#0a0f1d]/85 px-3.5 py-1.5 shadow-xl backdrop-blur-md font-mono text-[11px] text-slate-300">
            <span>
              <strong className="text-slate-500">LAT</strong> {telemetry.lat}° {telemetry.latDir}
            </span>
            <span className="text-white/20">|</span>
            <span>
              <strong className="text-slate-500">LNG</strong> {telemetry.lng}° {telemetry.lngDir}
            </span>
            <span className="text-white/20">|</span>
            <span>
              <strong className="text-slate-500">ALT</strong> {telemetry.altKm.toLocaleString()} KM
            </span>
          </div>
        </div>
      </div>

      {/* FLOATING INTENSITY LEGEND CARD */}
      <div className="pointer-events-auto absolute left-6 top-24 z-20 w-44 rounded-xl border border-white/15 bg-[#0a0f1d]/90 p-3.5 shadow-2xl backdrop-blur-md">
        <p className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400">
          Intensity
        </p>

        <div className="mt-2.5 space-y-2 text-xs">
          <div className="flex items-center gap-2 text-slate-200">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500 shadow-sm shadow-red-500/50" />
            <span>High intensity</span>
          </div>

          <div className="flex items-center gap-2 text-slate-200">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500" />
            <span>Medium / elevated</span>
          </div>

          <div className="flex items-center gap-2 text-slate-200">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span>Lower intensity</span>
          </div>

          <div className="flex items-center gap-2 text-slate-200">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400" />
            <span>Watch / flashpoint</span>
          </div>
        </div>

        <button
          onClick={() => setShowClassificationModal(true)}
          className="mt-3 flex items-center gap-1 font-mono text-[10px] text-slate-400 hover:text-white transition"
        >
          <span>How we classify</span>
          <ArrowRight className="h-2.5 w-2.5" />
        </button>
      </div>

      {/* FLOATING 3D ORBIT & ROTATION CONTROLS TOOLBAR */}
      <div className="pointer-events-auto absolute bottom-14 right-6 z-20 flex flex-col items-center gap-1.5 rounded-xl border border-white/20 bg-[#0a0f1d]/90 p-1.5 shadow-2xl backdrop-blur-md">
        {/* Zoom In */}
        <button
          onClick={() => orbitControlsRef.current.zoomIn()}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white shadow-sm transition hover:bg-white/20 hover:text-blue-400"
          title="Zoom In"
        >
          <Plus className="h-4 w-4" />
        </button>

        {/* Zoom Out */}
        <button
          onClick={() => orbitControlsRef.current.zoomOut()}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white shadow-sm transition hover:bg-white/20 hover:text-blue-400"
          title="Zoom Out"
        >
          <Minus className="h-4 w-4" />
        </button>

        <div className="my-0.5 h-px w-5 bg-white/15" />

        {/* 3D Perspective Tilt Cycle */}
        <button
          onClick={() => orbitControlsRef.current.cycleTilt()}
          className={`flex h-8 w-8 items-center justify-center rounded-lg border transition shadow-sm ${
            tiltPreset === "tactical"
              ? "border-blue-500/50 bg-blue-500/20 text-blue-300"
              : tiltPreset === "overhead"
              ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-300"
              : "border-purple-500/50 bg-purple-500/20 text-purple-300"
          }`}
          title={`3D Tilt: ${
            tiltPreset === "tactical"
              ? "Tactical 45° Orbit"
              : tiltPreset === "overhead"
              ? "Top-Down High Angle"
              : "Horizon Level"
          } (Click to toggle)`}
        >
          <Rotate3D className="h-4 w-4" />
        </button>

        {/* Reset View / North Up */}
        <button
          onClick={() => orbitControlsRef.current.resetView()}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 shadow-sm transition hover:bg-white/20 hover:text-white"
          title="Reset View (North Up)"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>

        {/* Auto-Rotate Cinematic Spin */}
        <button
          onClick={() => orbitControlsRef.current.toggleAutoRotate()}
          className={`flex h-8 w-8 items-center justify-center rounded-lg border transition shadow-sm ${
            isAutoRotating
              ? "border-red-500/60 bg-red-500/25 text-red-300"
              : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/20 hover:text-white"
          }`}
          title={isAutoRotating ? "Pause Auto-Rotation" : "Start 3D Cinematic Auto-Rotation"}
        >
          {isAutoRotating ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* QUICK REGION NAVIGATION BAR */}
      <div className="pointer-events-auto absolute left-6 bottom-14 z-20 hidden sm:flex items-center gap-1.5 rounded-lg border border-white/15 bg-[#0a0f1d]/85 p-1 backdrop-blur-md font-mono text-[10px]">
        <span className="px-2 font-bold uppercase tracking-wider text-slate-400">Jump To:</span>
        <button
          onClick={() => orbitControlsRef.current.goToRegion("europe")}
          className="rounded px-2.5 py-1 text-slate-300 hover:bg-white/10 hover:text-white transition"
        >
          Europe & Levant
        </button>
        <button
          onClick={() => orbitControlsRef.current.goToRegion("asia")}
          className="rounded px-2.5 py-1 text-slate-300 hover:bg-white/10 hover:text-white transition"
        >
          Asia-Pacific
        </button>
        <button
          onClick={() => orbitControlsRef.current.goToRegion("americas")}
          className="rounded px-2.5 py-1 text-slate-300 hover:bg-white/10 hover:text-white transition"
        >
          Americas
        </button>
      </div>

      {/* BOTTOM ATTRIBUTION LINE */}
      <div className="pointer-events-none absolute bottom-9 right-6 z-10 text-[10px] font-mono text-slate-400">
        Imagery: NASA Blue Marble via <span className="underline">GIBS</span> · Deaths: <span className="underline">UCDP</span> · Borders: Natural Earth
      </div>

      {/* BOTTOM NEWS DISPATCH TICKER */}
      <div className="pointer-events-auto absolute bottom-0 left-0 right-0 z-20 flex items-center border-t border-white/10 bg-[#070b14]/95 text-xs">
        <div className="flex shrink-0 items-center bg-red-600 px-3.5 py-1.5 font-mono text-[10px] font-black uppercase tracking-wider text-white">
          Latest
        </div>

        <div className="flex-1 overflow-hidden px-4 py-1.5 font-mono text-[11px] text-slate-300">
          <span className="font-bold text-blue-400 uppercase mr-2">{currentNews.source}</span>
          <span>{currentNews.text}</span>
        </div>
      </div>

      {/* METHODOLOGY CLASSIFICATION MODAL */}
      {showClassificationModal && (
        <div className="absolute inset-0 z-[600] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="relative max-w-lg rounded-2xl border border-white/20 bg-[#0d1424] p-6 shadow-2xl text-slate-200">
            <button
              onClick={() => setShowClassificationModal(false)}
              className="absolute right-4 top-4 rounded-lg p-1 text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-blue-400" />
              <h3 className="text-base font-bold text-white">Conflict Intensity Classification</h3>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Standardized methodology combining UCDP battle fatality reports, ACLED kinetic event telemetry, and strategic chokepoint threat matrices.
            </p>

            <div className="mt-4 space-y-3 text-xs">
              <div className="flex gap-3 rounded-lg border border-red-500/30 bg-red-950/20 p-2.5">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-red-500 mt-1" />
                <div>
                  <strong className="text-red-400">High Intensity</strong>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Sustained active kinetic warfare, artillery exchanges, airstrikes, &gt;1,000 battle-related fatalities annually.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 rounded-lg border border-orange-500/30 bg-orange-950/20 p-2.5">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-orange-500 mt-1" />
                <div>
                  <strong className="text-orange-400">Medium / Elevated</strong>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Active armed insurgencies, missile/drone interdictions, 100–999 fatalities annually.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-2.5">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-emerald-500 mt-1" />
                <div>
                  <strong className="text-emerald-400">Lower Intensity</strong>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Sporadic skirmishes, protected economic perimeters, &lt;100 fatalities annually.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 rounded-lg border border-sky-500/30 bg-sky-950/20 p-2.5">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-sky-400 mt-1" />
                <div>
                  <strong className="text-sky-400">Watch / Flashpoint</strong>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Strategic maritime chokepoints, ADIZ sorties, and high-risk deterrence standoffs with severe global contagion potential.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowClassificationModal(false)}
              className="mt-5 w-full rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white hover:bg-blue-500"
            >
              Close Methodology
            </button>
          </div>
        </div>
      )}

      {/* SLIDE-OUT THEATER DIRECTORY DRAWER */}
      {showDrawer && (
        <div className="absolute inset-y-0 left-0 z-[500] w-80 border-r border-white/15 bg-[#0a0f1d]/95 p-5 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white">Monitored Theaters</h3>
              <p className="text-[10px] text-slate-400 font-mono">29 ACTIVE SECTORS</p>
            </div>
            <button onClick={() => setShowDrawer(false)} className="rounded-md p-1 text-slate-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-3 max-h-[calc(100%-60px)] space-y-1.5 overflow-y-auto pr-1">
            {HOTSPOTS.map((h) => {
              const isSelected = selectedHotspot.id === h.id;
              const colorClass =
                h.intensity === "high"
                  ? "bg-red-500"
                  : h.intensity === "medium"
                  ? "bg-orange-500"
                  : h.intensity === "low"
                  ? "bg-emerald-500"
                  : "bg-sky-400";

              return (
                <div
                  key={h.id}
                  onClick={() => handleSelectDrawerTheater(h)}
                  className={`flex cursor-pointer items-center justify-between rounded-lg p-2.5 transition ${
                    isSelected ? "bg-white/15 border border-white/20" : "hover:bg-white/5 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`h-2 w-2 rounded-full ${colorClass}`} />
                    <div>
                      <p className="text-xs font-semibold text-white">{h.name}</p>
                      <p className="text-[10px] font-mono text-slate-400">
                        LAT {h.lat.toFixed(1)}° · LNG {h.lng.toFixed(1)}°
                      </p>
                    </div>
                  </div>

                  <span className="font-mono text-[10px] font-bold text-slate-400">
                    {h.score}/100
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
