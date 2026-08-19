"""
Davranışsal profil endpoint'leri.
Hafta 1'de sadece iskelet — Hafta 2-4'te gerçek anket/görüşme verisiyle,
Hafta 4-7'de MCDM (AHP+TOPSIS) ağırlıklarıyla doldurulacak.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Önerideki 5 davranışsal boyut
BEHAVIORAL_DIMENSIONS = [
    "emotional_patterns",       # Duygusal örüntüler
    "communication_style",      # İletişim tarzı
    "life_preferences",         # Yaşam tercihleri
    "decision_making_traits",   # Karar verme tarzı
    "relationship_dynamics",    # İlişki dinamikleri
]


class BehavioralProfile(BaseModel):
    subject_name: str
    dimensions: dict[str, str] = {}   # boyut -> ham metin/özet
    mcdm_weights: dict[str, float] | None = None  # AHP+TOPSIS sonrası doldurulur


@router.get("/dimensions")
def get_dimensions():
    """Anket ve MCDM sürecinde kullanılan 5 davranışsal boyutu döndürür."""
    return {"dimensions": BEHAVIORAL_DIMENSIONS}


@router.post("/")
def create_profile(profile: BehavioralProfile):
    """
    Geçici stub: gerçek implementasyonda PostgreSQL'e (behavioral_profile tablosu)
    yazılacak. Şimdilik alınan veriyi doğrulayıp geri döner.
    """
    return {"received": profile, "note": "TODO: persist to database (Week 2+)"}
