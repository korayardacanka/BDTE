"""
BDTE — MCDM (Multi-Criteria Decision Making) Module
=====================================================

NOTE: This file is backend/app/mcdm.py — the single source of truth for the
app. persona.py imports compute_ahp_weights() directly and computes weights
at runtime; weights are never manually synced in two places.

ml-pipeline/mcdm.py is a thin runner that imports this file, so you can run
the same report as a standalone script without starting the backend.

This script implements a two-stage MCDM process:

1. AHP (Analytic Hierarchy Process) — computes the relative importance of
   the 5 behavioral dimensions (emotional patterns, communication style,
   life preferences, decision-making traits, relationship dynamics) from
   a stakeholder's (family member's) pairwise comparisons. Output: a
   weight for each dimension (0-1, summing to 1) + a consistency ratio
   (CR — should be below 0.10, otherwise the comparisons are logically
   inconsistent).

2. TOPSIS — Given multiple candidate persona configurations (e.g. "more
   formal" vs "warmer" vs "balanced"), scores and ranks them using the
   AHP weights.

NOTE (important for the report): Due to time constraints, the pairwise
comparison values used for the seed persona are example/synthetic values
defined by the researcher to validate the methodology, not real survey
data from a family member (see backend/app/persona.py — SEED persona).
Every user-created persona, however, computes its weights from real
pairwise comparisons entered through the UI.
"""

import ahpy
import numpy as np
from pymcdm.methods import TOPSIS


# ---------------------------------------------------------------------------
# 1. AHP — compute the weights of the behavioral dimensions
# ---------------------------------------------------------------------------

# Pairwise comparisons use Saaty's 1-9 scale:
#   1 = equally important, 3 = slightly more important, 5 = strongly more
#   important, 7 = very strongly more important, 9 = extremely more
#   important (2, 4, 6, 8 = intermediate values).
# ('A', 'B'): x  →  A is x times more important than B.
#
# Example scenario (default/seed comparisons): a family member recalls
# their grandmother mostly through her "emotional patterns" and
# "communication style", while "decision-making traits" felt less
# defining in everyday conversation.
# NOTE: only the primary Saaty scale values (1, 3, 5, 7, 9) are used here —
# the frontend's comparison slider only offers these 5 steps per side.
# Intermediate values (2, 4, 6, 8) would not match any slider position and
# would crash the edit form, so they are avoided in default/seed data.
BEHAVIORAL_COMPARISONS = {
    ("emotional_patterns", "communication_style"): 3,
    ("emotional_patterns", "relationship_dynamics"): 3,
    ("emotional_patterns", "life_preferences"): 5,
    ("emotional_patterns", "decision_making_traits"): 7,
    ("communication_style", "relationship_dynamics"): 1,
    ("communication_style", "life_preferences"): 3,
    ("communication_style", "decision_making_traits"): 5,
    ("relationship_dynamics", "life_preferences"): 3,
    ("relationship_dynamics", "decision_making_traits"): 3,
    ("life_preferences", "decision_making_traits"): 3,
}


def compute_ahp_weights(comparisons: dict = BEHAVIORAL_COMPARISONS) -> dict:
    """
    Computes the weight vector and consistency ratio from pairwise
    comparisons using AHP.
    """
    compare = ahpy.Compare(name="behavioral_dimensions", comparisons=comparisons)
    weights = compare.target_weights  # {dimension: weight} — sums to 1.0
    cr = compare.consistency_ratio

    return {"weights": weights, "consistency_ratio": cr}


# ---------------------------------------------------------------------------
# 2. TOPSIS — rank alternative persona configurations using AHP weights
# ---------------------------------------------------------------------------

# Each alternative has a 1-10 "prominence" score for each of the 5
# dimensions (e.g., how strongly "emotional patterns" is expressed in that
# alternative). In a real application these scores would also come from
# stakeholder evaluation; here they are example/synthetic values.
ALTERNATIVE_CONFIGS = {
    "Warm and Emotional": {
        "emotional_patterns": 9, "communication_style": 8,
        "life_preferences": 6, "decision_making_traits": 4,
        "relationship_dynamics": 9,
    },
    "Balanced": {
        "emotional_patterns": 7, "communication_style": 7,
        "life_preferences": 7, "decision_making_traits": 6,
        "relationship_dynamics": 7,
    },
    "Practical and Informative": {
        "emotional_patterns": 4, "communication_style": 6,
        "life_preferences": 8, "decision_making_traits": 9,
        "relationship_dynamics": 5,
    },
}

DIMENSION_ORDER = [
    "emotional_patterns", "communication_style", "life_preferences",
    "decision_making_traits", "relationship_dynamics",
]


def compute_topsis_ranking(
    alternatives: dict = ALTERNATIVE_CONFIGS,
    weights: dict | None = None,
) -> list[tuple[str, float]]:
    """
    Ranks alternative persona configurations using TOPSIS, weighted by the
    AHP output. Higher score = closer to the ideal solution (better).
    """
    if weights is None:
        weights = compute_ahp_weights()["weights"]

    alt_names = list(alternatives.keys())
    matrix = np.array([
        [alternatives[name][dim] for dim in DIMENSION_ORDER]
        for name in alt_names
    ], dtype=float)

    weight_vector = np.array([weights[dim] for dim in DIMENSION_ORDER])
    # All dimensions are "profit" criteria — higher is always better.
    criteria_types = np.array([1] * len(DIMENSION_ORDER))  # 1 = profit, -1 = cost

    topsis = TOPSIS()
    scores = topsis(matrix, weight_vector, criteria_types)

    ranked = sorted(zip(alt_names, scores), key=lambda x: x[1], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Runnable demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("1) AHP — Behavioral Dimension Weights")
    print("=" * 60)
    ahp_result = compute_ahp_weights()
    for dim, w in sorted(ahp_result["weights"].items(), key=lambda x: -x[1]):
        print(f"  {dim:28s} {w:.4f}")
    cr = ahp_result["consistency_ratio"]
    status = "OK — CONSISTENT" if cr < 0.10 else "WARNING — INCONSISTENT (CR >= 0.10, review comparisons)"
    print(f"\n  Consistency Ratio (CR): {cr:.4f}  ->  {status}")

    print("\n" + "=" * 60)
    print("2) TOPSIS — Alternative Persona Configuration Ranking")
    print("=" * 60)
    ranking = compute_topsis_ranking(weights=ahp_result["weights"])
    for i, (name, score) in enumerate(ranking, start=1):
        print(f"  {i}. {name:28s} score: {score:.4f}")

    print(f"\n  -> Selected configuration: '{ranking[0][0]}'")
    print("    (persona.py's seed persona is aligned with these weights)")
