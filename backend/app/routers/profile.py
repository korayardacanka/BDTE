"""
Behavioral profile (persona) endpoints.

Multiple personas are supported. When a persona is created or edited, the
user makes 10 pairwise comparisons across the 5 dimensions (Saaty scale);
the backend uses AHP to compute weights CUSTOM to that persona (no
fixed/shared weights are used).
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.mcdm import compute_ahp_weights, compute_topsis_ranking
from app.models import BehavioralProfile, ConversationMessage
from app.persona import COMPARISON_PAIRS, DIMENSION_KEYS, DIMENSION_LABELS, profile_row_to_dict

router = APIRouter()


@router.get("/dimensions")
def get_dimensions():
    """Returns the 5 behavioral dimensions and their labels (for building the form)."""
    return {
        "dimensions": DIMENSION_KEYS,
        "labels": DIMENSION_LABELS,
        "comparison_pairs": COMPARISON_PAIRS,
    }


@router.get("/")
def list_profiles(db: Session = Depends(get_db)):
    """Lists all saved personas (summary view)."""
    profiles = db.query(BehavioralProfile).order_by(BehavioralProfile.id).all()
    return [
        {
            "id": p.id,
            "subject_name": p.subject_name,
            "relation": p.relation,
            "age_at_reference": p.age_at_reference,
            "gender": p.gender,
            "consistency_ratio": p.consistency_ratio,
        }
        for p in profiles
    ]


@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Returns full details of a single persona (dimensions + weights + raw comparisons)."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona not found")
    result = profile_row_to_dict(profile) | {"id": profile.id}
    result["comparisons"] = json.loads(profile.comparisons_json) if profile.comparisons_json else None
    return result


class ComparisonEntry(BaseModel):
    """
    A single pairwise comparison entry.
    value: a number from 1-9 on the Saaty scale.
    more_important: "a" or "b" — which one is more important.
    """
    a: str
    b: str
    value: float = Field(ge=1, le=9)
    more_important: str  # "a" or "b"


class ProfileRequest(BaseModel):
    subject_name: str
    relation: str
    gender: str  # "female" or "male"
    age_at_reference: int | None = None
    dimensions: dict[str, str]  # 5 dimensions -> free text
    comparisons: list[ComparisonEntry]  # exactly 10 comparisons expected


def _validate_and_compute(req: ProfileRequest) -> tuple[dict, float]:
    """Validates the input and computes AHP weights. Raises HTTPException on error."""
    if req.gender not in ("female", "male"):
        raise HTTPException(status_code=400, detail="gender must be 'female' or 'male'")
    missing = [k for k in DIMENSION_KEYS if not req.dimensions.get(k, "").strip()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing dimensions: {', '.join(missing)}")
    if len(req.comparisons) != len(COMPARISON_PAIRS):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(COMPARISON_PAIRS)} pairwise comparisons, got {len(req.comparisons)}.",
        )

    comparisons_dict: dict[tuple, float] = {}
    for c in req.comparisons:
        if c.more_important == "a":
            comparisons_dict[(c.a, c.b)] = c.value
        elif c.more_important == "b":
            comparisons_dict[(c.a, c.b)] = 1 / c.value
        else:
            raise HTTPException(status_code=400, detail="more_important must be 'a' or 'b'")

    try:
        ahp_result = compute_ahp_weights(comparisons=comparisons_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"AHP computation error: {exc}")

    weights = {k: float(v) for k, v in ahp_result["weights"].items()}
    cr = float(ahp_result["consistency_ratio"])
    return weights, cr


def _apply_to_profile(profile: BehavioralProfile, req: ProfileRequest, weights: dict, cr: float) -> None:
    profile.subject_name = req.subject_name
    profile.relation = req.relation
    profile.gender = req.gender
    profile.age_at_reference = req.age_at_reference
    profile.emotional_patterns = req.dimensions["emotional_patterns"]
    profile.communication_style = req.dimensions["communication_style"]
    profile.life_preferences = req.dimensions["life_preferences"]
    profile.decision_making_traits = req.dimensions["decision_making_traits"]
    profile.relationship_dynamics = req.dimensions["relationship_dynamics"]
    profile.weight_emotional_patterns = weights.get("emotional_patterns", 0)
    profile.weight_communication_style = weights.get("communication_style", 0)
    profile.weight_life_preferences = weights.get("life_preferences", 0)
    profile.weight_decision_making_traits = weights.get("decision_making_traits", 0)
    profile.weight_relationship_dynamics = weights.get("relationship_dynamics", 0)
    profile.consistency_ratio = cr
    profile.comparisons_json = json.dumps([c.model_dump() for c in req.comparisons])

    # TOPSIS: rank this persona's weights against predefined behavioral
    # archetypes to find the closest match — a validation/insight step
    # described in the project proposal (AHP derives weights, TOPSIS
    # validates them against alternative configurations).
    topsis_ranking = compute_topsis_ranking(weights=weights)
    profile.closest_archetype = topsis_ranking[0][0]
    profile.closest_archetype_score = float(topsis_ranking[0][1])


@router.post("/")
def create_profile(req: ProfileRequest, db: Session = Depends(get_db)):
    weights, cr = _validate_and_compute(req)

    profile = BehavioralProfile()
    _apply_to_profile(profile, req, weights, cr)
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "subject_name": profile.subject_name,
        "weights": weights,
        "consistency_ratio": cr,
        "consistency_ok": bool(cr < 0.10),
        "closest_archetype": profile.closest_archetype,
        "closest_archetype_score": profile.closest_archetype_score,
    }


@router.put("/{profile_id}")
def update_profile(profile_id: int, req: ProfileRequest, db: Session = Depends(get_db)):
    """Edits an existing persona; weights are recomputed from the new comparisons."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona not found")

    weights, cr = _validate_and_compute(req)
    _apply_to_profile(profile, req, weights, cr)
    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "subject_name": profile.subject_name,
        "weights": weights,
        "consistency_ratio": cr,
        "consistency_ok": bool(cr < 0.10),
        "closest_archetype": profile.closest_archetype,
        "closest_archetype_score": profile.closest_archetype_score,
    }


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Deletes a persona and its associated conversation history."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona not found")

    remaining = db.query(BehavioralProfile).count()
    if remaining <= 1:
        raise HTTPException(
            status_code=400,
            detail="At least one persona must remain — the last persona cannot be deleted.",
        )

    # Clean up the associated conversation history too (session_id format "...::personaX").
    db.query(ConversationMessage).filter(
        ConversationMessage.session_id.like(f"%::persona{profile_id}")
    ).delete(synchronize_session=False)

    db.delete(profile)
    db.commit()
    return {"deleted": profile_id}
