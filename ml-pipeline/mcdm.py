"""
BDTE — MCDM Report Runner
===========================

The actual AHP/TOPSIS logic lives in backend/app/mcdm.py (single source of
truth — persona.py also pulls weights from there at runtime). This script
is a thin runner for people who just want to see the MCDM report in the
terminal without starting the backend.

To run, the backend's virtual environment must be active (ahpy, pymcdm,
numpy must be installed):

    cd backend && .venv\\Scripts\\activate   (Windows)
    cd ../ml-pipeline
    python mcdm.py
"""
import os
import sys

# Add the backend/ folder to the Python path so "app.mcdm" can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.mcdm import compute_ahp_weights, compute_topsis_ranking  # noqa: E402

if __name__ == "__main__":
    print("=" * 60)
    print("1) AHP — Behavioral Dimension Weights")
    print("=" * 60)
    ahp_result = compute_ahp_weights()
    for dim, w in sorted(ahp_result["weights"].items(), key=lambda x: -x[1]):
        print(f"  {dim:28s} {w:.4f}")
    cr = ahp_result["consistency_ratio"]
    status = "OK — CONSISTENT" if cr < 0.10 else "WARNING — INCONSISTENT (CR >= 0.10)"
    print(f"\n  Consistency Ratio (CR): {cr:.4f}  ->  {status}")

    print("\n" + "=" * 60)
    print("2) TOPSIS — Alternative Persona Configuration Ranking")
    print("=" * 60)
    ranking = compute_topsis_ranking(weights=ahp_result["weights"])
    for i, (name, score) in enumerate(ranking, start=1):
        print(f"  {i}. {name:28s} score: {score:.4f}")

    print(f"\n  -> Selected configuration: '{ranking[0][0]}'")
    print("    (persona.py now uses these weights AUTOMATICALLY)")
