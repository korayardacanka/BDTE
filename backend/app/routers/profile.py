"""
Davranışsal profil endpoint'leri.

Şu an EXAMPLE_PERSONA (persona.py) sabit/örnek veri olarak kullanılıyor —
gerçek katılımcı verisi yerine, zaman kısıtı nedeniyle sentetik bir profil
üzerinden MCDM + prompt engineering metodolojisi doğrulanıyor.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.persona import EXAMPLE_PERSONA

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
    dimensions: dict[str, str] = {}
    mcdm_weights: dict[str, float] | None = None


@router.get("/dimensions")
def get_dimensions():
    """Anket ve MCDM sürecinde kullanılan 5 davranışsal boyutu döndürür."""
    return {"dimensions": BEHAVIORAL_DIMENSIONS}


@router.get("/")
def get_current_profile():
    """Şu an sistemde aktif olan (örnek/sentetik) davranışsal profili döndürür."""
    return EXAMPLE_PERSONA


@router.post("/")
def create_profile(profile: BehavioralProfile):
    """
    TODO: Gerçek implementasyonda PostgreSQL'e (behavioral_profile tablosu)
    yazılacak ve chat.py bu profili kullanacak şekilde güncellenecek.
    """
    return {"received": profile, "note": "TODO: persist to database"}