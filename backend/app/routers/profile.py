"""
Davranışsal profil (persona) endpoint'leri.

Birden fazla persona desteklenir. Her persona oluşturulurken/düzenlenirken,
kullanıcı 5 boyut arasında 10 ikili karşılaştırma yapar (Saaty ölçeği,
1/9 - 9 arası); backend bunlardan AHP ile o persona'ya ÖZEL ağırlıkları
hesaplar (sabit/genel ağırlıklar kullanılmaz).
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.mcdm import compute_ahp_weights
from app.models import BehavioralProfile, ConversationMessage
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
            "gender": p.gender,
            "consistency_ratio": p.consistency_ratio,
        }
        for p in profiles
    ]


@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Tek bir persona'nın tüm detaylarını (boyutlar + ağırlıklar + ham karşılaştırmalar) döndürür."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona bulunamadı")
    result = profile_row_to_dict(profile) | {"id": profile.id}
    result["comparisons"] = json.loads(profile.comparisons_json) if profile.comparisons_json else None
    return result


class ComparisonEntry(BaseModel):
    """
    Tek bir ikili karşılaştırma girdisi.
    value: Saaty ölçeğinde 1-9 arası bir sayı.
    more_important: "a" veya "b" — hangisinin daha önemli olduğu.
    """
    a: str
    b: str
    value: float = Field(ge=1, le=9)
    more_important: str  # "a" veya "b"


class ProfileRequest(BaseModel):
    subject_name: str
    relation: str
    gender: str  # "kadın" veya "erkek"
    age_at_reference: int | None = None
    dimensions: dict[str, str]  # 5 boyut -> serbest metin
    comparisons: list[ComparisonEntry]  # tam olarak 10 karşılaştırma bekleniyor


def _validate_and_compute(req: ProfileRequest) -> tuple[dict, float]:
    """Girdiyi doğrular, AHP ağırlıklarını hesaplar. Hata varsa HTTPException fırlatır."""
    if req.gender not in ("kadın", "erkek"):
        raise HTTPException(status_code=400, detail="gender 'kadın' veya 'erkek' olmalı")
    missing = [k for k in DIMENSION_KEYS if not req.dimensions.get(k, "").strip()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Eksik boyutlar: {', '.join(missing)}")
    if len(req.comparisons) != len(COMPARISON_PAIRS):
        raise HTTPException(
            status_code=400,
            detail=f"{len(COMPARISON_PAIRS)} ikili karşılaştırma bekleniyor, {len(req.comparisons)} geldi.",
        )

    comparisons_dict: dict[tuple, float] = {}
    for c in req.comparisons:
        if c.more_important == "a":
            comparisons_dict[(c.a, c.b)] = c.value
        elif c.more_important == "b":
            comparisons_dict[(c.a, c.b)] = 1 / c.value
        else:
            raise HTTPException(status_code=400, detail="more_important 'a' veya 'b' olmalı")

    try:
        ahp_result = compute_ahp_weights(comparisons=comparisons_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"AHP hesaplama hatası: {exc}")

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
    }


@router.put("/{profile_id}")
def update_profile(profile_id: int, req: ProfileRequest, db: Session = Depends(get_db)):
    """Var olan bir persona'yı düzenler; ağırlıklar yeni karşılaştırmalardan yeniden hesaplanır."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona bulunamadı")

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
    }


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Bir persona'yı ve ona ait sohbet geçmişini siler."""
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Persona bulunamadı")

    remaining = db.query(BehavioralProfile).count()
    if remaining <= 1:
        raise HTTPException(
            status_code=400,
            detail="En az bir persona kalmalı — son persona silinemez.",
        )

    # İlgili sohbet geçmişini de temizle (session_id "...::personaX" formatında).
    db.query(ConversationMessage).filter(
        ConversationMessage.session_id.like(f"%::persona{profile_id}")
    ).delete(synchronize_session=False)

    db.delete(profile)
    db.commit()
    return {"deleted": profile_id}
