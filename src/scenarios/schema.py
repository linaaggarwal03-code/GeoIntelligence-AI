"""
Data schemas and validation contracts for What-If Geopolitical Simulator.
Defines structured classes for scenario definitions, country impact results, and dyadic changes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.scenarios.config import DEFAULT_DECAY_FACTOR, DEFAULT_PROPAGATION_DEPTH


@dataclass
class ScenarioDefinition:
    """
    User/policy scenario parameter specifications for a counterfactual simulation.
    """
    scenario_id: str
    name: str
    target_country_iso3: str
    description: str = ""
    target_dyad: Optional[Tuple[str, str]] = None
    archetype: Optional[str] = None
    tone_delta: float = 0.0
    conflict_news_multiplier: float = 1.0
    tension_delta: Optional[float] = None
    sever_dyadic_tie: bool = False
    propagation_depth: int = DEFAULT_PROPAGATION_DEPTH
    decay_factor: float = DEFAULT_DECAY_FACTOR

    def validate(self, reference_countries: List[str], valid_dyads: List[Tuple[str, str]]) -> None:
        """
        Validate scenario parameters against strict integrity and domain bounds.
        """
        ref_set = set(reference_countries)

        # 1. Target country validation
        if not self.target_country_iso3 or self.target_country_iso3 not in ref_set:
            raise ValueError(
                f"Invalid target_country_iso3: '{self.target_country_iso3}'. "
                f"Must be a recognized code from the {len(reference_countries)} reference countries."
            )

        # 2. Target dyad validation
        if self.target_dyad is not None:
            if not isinstance(self.target_dyad, (tuple, list)) or len(self.target_dyad) != 2:
                raise ValueError("target_dyad must be a tuple/list of exactly two distinct country ISO3 codes.")
            c_a, c_b = self.target_dyad[0], self.target_dyad[1]
            if c_a == c_b:
                raise ValueError(f"target_dyad cannot be self-referential: ({c_a}, {c_b}).")
            if c_a not in ref_set or c_b not in ref_set:
                raise ValueError(f"target_dyad countries ({c_a}, {c_b}) must both be valid reference countries.")

        # 3. tension_delta requires explicit target_dyad
        if self.tension_delta is not None and self.target_dyad is None:
            raise ValueError(
                "tension_delta is only valid when target_dyad is explicitly provided; "
                "cannot infer an arbitrary dyad from target_country_iso3."
            )

        # 4. sever_dyadic_tie requires explicit target_dyad and must exist
        if self.sever_dyadic_tie:
            if self.target_dyad is None:
                raise ValueError("sever_dyadic_tie requires an explicit target_dyad.")
            # Check if target_dyad exists in empirical dyads (either directed or undirected)
            canonical_dyads = {
                (d[0], d[1]) for d in valid_dyads
            } | {
                (min(d[0], d[1]), max(d[0], d[1])) for d in valid_dyads
            }
            c_a, c_b = self.target_dyad[0], self.target_dyad[1]
            if (c_a, c_b) not in canonical_dyads and (min(c_a, c_b), max(c_a, c_b)) not in canonical_dyads:
                raise ValueError(
                    f"Cannot sever non-existent empirical dyad: ({c_a}, {c_b}). "
                    "The dyad does not exist in the baseline relationship network."
                )

        # 5. Multiplier validation
        if self.conflict_news_multiplier < 0.0:
            raise ValueError(f"conflict_news_multiplier must be non-negative, got {self.conflict_news_multiplier}.")

        # 6. Propagation depth validation
        if self.propagation_depth < 0:
            raise ValueError(f"propagation_depth must be >= 0, got {self.propagation_depth}.")

        # 7. Decay factor validation
        if not (0.0 <= self.decay_factor <= 1.0):
            raise ValueError(f"decay_factor must be in [0.0, 1.0], got {self.decay_factor}.")


@dataclass
class SimulationResult:
    """
    Complete output container for a counterfactual scenario simulation.
    """
    scenario: ScenarioDefinition
    baseline_metadata: Dict[str, Any]
    country_impacts: List[Dict[str, Any]]
    dyad_impacts: List[Dict[str, Any]]
    graph_json: Dict[str, Any]
    summary: Dict[str, Any]
