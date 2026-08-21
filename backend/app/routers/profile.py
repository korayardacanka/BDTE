"""
Davranışsal profil (persona) endpoint'leri.

Artık birden fazla persona desteklenir. Her yeni persona oluşturulurken,
kullanıcı 5 boyut arasında 10 ikili karşılaştırma yapar (Saaty ölçeği,
1/9 - 9 arası); backend bunlardan AHP ile o persona'ya ÖZEL ağırlıkları
hesaplar (sabit/genel ağırlıklar kullanılmaz).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.mcdm import compute_ahp_weights
from app.models import BehavioralProfile
from app.persona import COMPARISON_PAIRS, DIMENSION_KEYS, DIMENSION_LABELS, profile_row_to_dict

router = APIRouter()


@router.get("/dimensions")
def get_dimensions():
    """5 davranışsal boyutu ve etiketlerini döndürür (form oluşturmak için)."""
    return {
        "dimensions": DIMENSION_KEYS,
        "labels": DIMENSION_LABELS,
        "comparison_pairs": COMPARISON_PAIRS,
    }


@router.get("/")
def list_profiles(db: Session = Depends(get_db)):
    """Tüm kayıtlı persona'ları (özet halinde) listeler."""
    profiles = db.query(BehavioralProfile).order_by(BehavioralProfile.id).all()
    return [
        {
            "id": p.id,
            "subject_name": p.subject_name,
            "relation": p.relation,
            "age_at_reference": p.age_at_reference,
            "consistency_ratio": p.consistency_ratio,
        }
        for p in profiles
    ]


@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Tek bir persona'nın tüm detaylarını (boyutlar + ağırlıklar) döndürür."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona bulunamadı")
    return profile_row_to_dict(profile) | {"id": profile.id}


class ComparisonEntry(BaseModel):
    """
    Tek bir ikili karşılaştırma girdisi.
    value: Saaty ölçeğinde 1-9 arası bir sayı.
    more_important: "a" veya "b" — hangisinin daha önemli olduğu.
    (a == b ise / value == 1 ise "eşit önemde" demektir.)
    """
    a: str
    b: str
    value: float = Field(ge=1, le=9)
    more_important: str  # "a" veya "b"


class CreateProfileRequest(BaseModel):
    subject_name: str
    relation: str
    age_at_reference: int | None = None
    dimensions: dict[str, str]  # 5 boyut -> serbest metin
    comparisons: list[ComparisonEntry]  # tam olarak 10 karşılaştırma bekleniyor


@router.post("/")
def create_profile(req: CreateProfileRequest, db: Session = Depends(get_db)):
    # Girdi doğrulama
    missing = [k for k in DIMENSION_KEYS if not req.dimensions.get(k, "").strip()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Eksik boyutlar: {', '.join(missing)}",
        )
    if len(req.comparisons) != len(COMPARISON_PAIRS):
        raise HTTPException(
            status_code=400,
            detail=f"{len(COMPARISON_PAIRS)} ikili karşılaştırma bekleniyor, {len(req.comparisons)} geldi.",
        )

    # Karşılaştırmaları ahpy formatına çevir: (A, B): x  →  A, B'den x kat önemli.
    comparisons_dict: dict[tuple, float] = {}
    for c in req.comparisons:
        if c.more_important == "a":
            comparisons_dict[(c.a, c.b)] = c.value
        elif c.more_important == "b":
            comparisons_dict[(c.a, c.b)] = 1 / c.value
        else:
            raise HTTPException(status_code=400, detail="more_important 'a' veya 'b' olmalı")

    # AHP ile bu persona'ya ÖZEL ağırlıkları hesapla.
    try:
        ahp_result = compute_ahp_weights(comparisons=comparisons_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"AHP hesaplama hatası: {exc}")

    weights = {k: float(v) for k, v in ahp_result["weights"].items()}
    cr = float(ahp_result["consistency_ratio"])

    profile = BehavioralProfile(
        subject_name=req.subject_name,
        relation=req.relation,
        age_at_reference=req.age_at_reference,
        emotional_patterns=req.dimensions["emotional_patterns"],
        communication_style=req.dimensions["communication_style"],
        life_preferences=req.dimensions["life_preferences"],
        decision_making_traits=req.dimensions["decision_making_traits"],
        relationship_dynamics=req.dimensions["relationship_dynamics"],
        weight_emotional_patterns=weights.get("emotional_patterns", 0),
        weight_communication_style=weights.get("communication_style", 0),
        weight_life_preferences=weights.get("life_preferences", 0),
        weight_decision_making_traits=weights.get("decision_making_traits", 0),
        weight_relationship_dynamics=weights.get("relationship_dynamics", 0),
        consistency_ratio=cr,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "subject_name": profile.subject_name,
        "weights": weights,
        "consistency_ratio": cr,
        "consistency_ok": bool(cr < 0.10),
    }