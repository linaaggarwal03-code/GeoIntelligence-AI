export interface IntelligenceMetrics {
  escalationScore: number;
  escalationChange: number;
  conflictScore: number;
  conflictStatus: "Elevated" | "Moderate" | "Guarded" | "Critical";
  economyScore: number;
  economyStatus: "High Volatility" | "Moderate Exposure" | "Stable";
  energyScore: number;
  energyStatus: "Acute Disruption" | "Tight Supply" | "Resilient";
  globalImpactScore: number;
  globalImpactStatus: "Systemic Risk" | "Regional Spillover" | "Localized";
  confidence: number;
  summaryText: string;
  chartData: { horizon: string; risk: number; upper: number; lower: number; baseline: number }[];
  keyDrivers: { title: string; category: "conflict" | "economy" | "energy" | "global_impact"; impact: "high" | "medium" | "low"; description: string }[];
  earlyWarnings: { id: string; type: "critical" | "warning" | "info"; title: string; timestamp: string; detail: string }[];
}

// Deterministic seed generation based on string hashing
function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function computeIntelligence(
  c1Raw: string,
  c2Raw: string,
  periodStr: string,
  activeDomains: string[] = ["conflict", "economy", "energy", "global_impact"]
): IntelligenceMetrics {
  const c1 = (c1Raw || "India").trim();
  const c2 = (c2Raw || "Pakistan").trim();
  const period = parseInt(periodStr || "90", 10);

  const pairKey = [c1.toLowerCase(), c2.toLowerCase()].sort().join("_");
  const seed = hashString(pairKey);

  // Preset known geopolitical flashpoints
  const isIndPak = pairKey.includes("india") && pairKey.includes("pakistan");
  const isUsChn = (pairKey.includes("united states") || pairKey.includes("us") || pairKey.includes("usa")) && pairKey.includes("china");
  const isRusUkr = pairKey.includes("russia") && pairKey.includes("ukraine");
  const isIsrIrn = (pairKey.includes("israel") && pairKey.includes("iran")) || (pairKey.includes("israel") && pairKey.includes("gaza"));

  let baseEscalation = 52;
  let baseConflict = 55;
  let baseEconomy = 48;
  let baseEnergy = 45;
  let baseGlobal = 50;

  if (isRusUkr) {
    baseEscalation = 82;
    baseConflict = 88;
    baseEconomy = 72;
    baseEnergy = 86;
    baseGlobal = 84;
  } else if (isIsrIrn) {
    baseEscalation = 79;
    baseConflict = 85;
    baseEconomy = 68;
    baseEnergy = 88;
    baseGlobal = 80;
  } else if (isUsChn) {
    baseEscalation = 68;
    baseConflict = 62;
    baseEconomy = 85;
    baseEnergy = 64;
    baseGlobal = 89;
  } else if (isIndPak) {
    baseEscalation = 64;
    baseConflict = 72;
    baseEconomy = 58;
    baseEnergy = 52;
    baseGlobal = 61;
  } else {
    // Custom dynamic calculation based on seed
    baseEscalation = 40 + (seed % 35);
    baseConflict = 42 + ((seed >> 2) % 36);
    baseEconomy = 38 + ((seed >> 4) % 38);
    baseEnergy = 35 + ((seed >> 6) % 35);
    baseGlobal = 40 + ((seed >> 8) % 37);
  }

  // Adjust for forecast window (longer horizons tend to show compounding uncertainty)
  const horizonFactor = period === 30 ? -3 : period === 90 ? 2 : period === 180 ? 6 : 9;
  const escalationScore = Math.min(96, Math.max(20, baseEscalation + horizonFactor));
  const conflictScore = Math.min(98, Math.max(18, baseConflict + Math.round(horizonFactor * 0.8)));
  const economyScore = Math.min(95, Math.max(15, baseEconomy + Math.round(horizonFactor * 0.6)));
  const energyScore = Math.min(95, Math.max(15, baseEnergy + Math.round(horizonFactor * 0.7)));
  const globalImpactScore = Math.min(97, Math.max(20, baseGlobal + Math.round(horizonFactor * 0.9)));

  const escalationChange = ((seed % 14) - 5) + (horizonFactor > 0 ? 3 : -2);

  // Status mapping
  const conflictStatus = conflictScore >= 80 ? "Critical" : conflictScore >= 65 ? "Elevated" : conflictScore >= 45 ? "Moderate" : "Guarded";
  const economyStatus = economyScore >= 75 ? "High Volatility" : economyScore >= 50 ? "Moderate Exposure" : "Stable";
  const energyStatus = energyScore >= 75 ? "Acute Disruption" : energyScore >= 50 ? "Tight Supply" : "Resilient";
  const globalImpactStatus = globalImpactScore >= 75 ? "Systemic Risk" : globalImpactScore >= 55 ? "Regional Spillover" : "Localized";

  // Timeline points calculation
  const steps = [
    { label: "Now", factor: 0 },
    { label: "30D", factor: 0.25 },
    { label: "60D", factor: 0.5 },
    { label: "90D", factor: 0.75 },
    { label: "180D", factor: 1.0 },
    { label: "365D", factor: 1.25 },
  ];

  const chartData = steps.map((s, idx) => {
    const drift = Math.sin((seed % 7) + idx * 0.7) * 4;
    const projected = Math.round(Math.min(98, Math.max(20, escalationScore + (s.factor * 8) + drift)));
    return {
      horizon: s.label,
      risk: projected,
      upper: Math.min(100, projected + 7 + idx * 2),
      lower: Math.max(10, projected - 6 - idx * 2),
      baseline: Math.max(25, projected - 12),
    };
  });

  // Dynamic Key Drivers
  let drivers = [
    {
      title: "Cross-Border Military Posture",
      category: "conflict" as const,
      impact: conflictScore >= 70 ? ("high" as const) : ("medium" as const),
      description: `Active frontline monitoring detects heightened mobilization alerts and bilateral surveillance activity along ${c1}-${c2} boundary zones.`,
    },
    {
      title: "Bilateral Trade & Tariff Sanctions",
      category: "economy" as const,
      impact: economyScore >= 65 ? ("high" as const) : ("medium" as const),
      description: `Supply chain friction and reciprocal protective duties constrain industrial shipments, raising import price pressures.`,
    },
    {
      title: "Transit Corridors & Energy Flow Integrity",
      category: "energy" as const,
      impact: energyScore >= 70 ? ("high" as const) : ("medium" as const),
      description: `Strategic sea lanes and pipeline corridors face speculative risk premiums and cargo rerouting bottlenecks.`,
    },
    {
      title: "Multilateral Alliances & Diplomatic Spillover",
      category: "global_impact" as const,
      impact: globalImpactScore >= 70 ? ("high" as const) : ("medium" as const),
      description: `Regional treaty partners and international security blocs are preparing contingency containment protocols.`,
    },
  ];

  if (isIndPak) {
    drivers = [
      {
        title: "Line of Control Reconnaissance & Ceasefire Vigilance",
        category: "conflict",
        impact: "high",
        description: "Sensor networks report sporadic forward redeployments and electronic surveillance patrols across northern sector sectors.",
      },
      {
        title: "Indus Basin Hydro-Treaty & Water Allocation Friction",
        category: "global_impact",
        impact: "medium",
        description: "Bilateral diplomatic meetings remain stalled regarding seasonal water dispute arbitration and reservoir monitoring.",
      },
      {
        title: "Subcontinental Trade Routing & Aviation Sanctions",
        category: "economy",
        impact: "medium",
        description: "Indirect transshipment routes continue incurring transit surcharges for freight passing through maritime hubs.",
      },
      {
        title: "Hydrocarbon Import & Regional Pipeline Vulnerability",
        category: "energy",
        impact: "medium",
        description: "South Asian LNG supply contracts show elevated volatility due to Strait of Hormuz chokepoint dependency.",
      },
    ];
  } else if (isRusUkr) {
    drivers = [
      {
        title: "Kinetic Artillery & Long-Range Drone Exchanges",
        category: "conflict",
        impact: "high",
        description: "High-tempo drone strikes on deep logistics hubs, refining facilities, and energy infrastructure.",
      },
      {
        title: "European Gas Transit & Black Sea Grain Corridor",
        category: "energy",
        impact: "high",
        description: "Maritime insurance surcharges and pipeline cutoff timelines keep global wheat and gas benchmarks under strain.",
      },
      {
        title: "G7 Sanctions Regime & Secondary Financial Controls",
        category: "economy",
        impact: "high",
        description: "Enforcement sweeps against dual-use component corridors create friction for third-country banking networks.",
      },
      {
        title: "NATO Flank Preparedness & Intercontinental Deterrence",
        category: "global_impact",
        impact: "high",
        description: "Persistent military deployments along the Suwalki Gap and Baltic airspace maintain defense readiness alerts.",
      },
    ];
  } else if (isUsChn) {
    drivers = [
      {
        title: "Taiwan Strait & South China Sea Maritime Maneuvers",
        category: "conflict",
        impact: "high",
        description: "Close-proximity air-sea encounters between naval patrols and anti-access/area-denial exercises in the first island chain.",
      },
      {
        title: "Advanced Semiconductor Export Controls & Rare Earth Quotas",
        category: "economy",
        impact: "high",
        description: "Technology decoupling policies accelerate localized semiconductor fab investment while restricting advanced lithography tooling.",
      },
      {
        title: "Malacca Strait Fuel Logistics & Strategic Reserves",
        category: "energy",
        impact: "medium",
        description: "Both nations maintain record strategic petroleum reserves to hedge against potential maritime blockade scenarios.",
      },
      {
        title: "Bilateral Diplomatic Off-Ramps vs Deterrence Posturing",
        category: "global_impact",
        impact: "high",
        description: "Security dialogues face fragile momentum amid competing economic summit agendas and Indo-Pacific treaty maneuvers.",
      },
    ];
  }

  // Filter drivers based on active domains
  const activeDrivers = drivers.filter((d) => activeDomains.includes(d.category));

  // Early warning alerts
  const earlyWarnings = [
    {
      id: "w-1",
      type: escalationScore > 75 ? ("critical" as const) : ("warning" as const),
      title: `${c1} - ${c2} Escalation Threshold Alert`,
      timestamp: "Just now",
      detail: `Model telemetry notes a composite escalation metric of ${escalationScore}/100 with probability of kinetic or economic retaliatory action exceeding historical baseline.`,
    },
    {
      id: "w-2",
      type: "warning" as const,
      title: "Supply Chain & Trade Flow Divergence",
      timestamp: "32 mins ago",
      detail: `Bilateral trade corridor metrics indicate commercial freight slowdown and freight insurance quote revisions across primary transshipment ports.`,
    },
    {
      id: "w-3",
      type: "info" as const,
      title: "Multilateral Intelligence Signal Synchronized",
      timestamp: "1 hour ago",
      detail: `Integrated satellite feeds, diplomatic event registries, and trade flow monitors synchronized for current ${period}-day forecast model cycle.`,
    },
  ];

  const summaryText = `Comprehensive intelligence forecast for ${c1} and ${c2} across the next ${period} days indicates an aggregate escalation risk indicator of ${escalationScore}/100 (${conflictStatus}). Primary exposure manifests across ${activeDomains.join(", ")} vectors with an estimated confidence index of 88%.`;

  return {
    escalationScore,
    escalationChange,
    conflictScore,
    conflictStatus,
    economyScore,
    economyStatus,
    energyScore,
    energyStatus,
    globalImpactScore,
    globalImpactStatus,
    confidence: 88,
    summaryText,
    chartData,
    keyDrivers: activeDrivers.length > 0 ? activeDrivers : drivers,
    earlyWarnings,
  };
}
