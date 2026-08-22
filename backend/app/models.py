"""
SQLAlchemy modelleri (veritabanı tabloları).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class ConversationMessage(Base):
    """Her sohbet mesajını (kullanıcı ve asistan) kalıcı olarak saklar."""

    __tablename__ = "conversation_log"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # "user" veya "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BehavioralProfile(Base):
    """
    Davranışsal profil kaydı. Her persona, kendi ikili karşılaştırmalarından
    (AHP) hesaplanmış KİŞİYE ÖZEL ağırlıklara sahiptir — sabit/genel
    ağırlıklar kullanılmaz. Bu, projenin MCDM metodolojisinin temelidir.
    """

    __tablename__ = "behavioral_profile"

    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(128), nullable=False)
    relation = Column(String(64), nullable=True)
    gender = Column(String(16), nullable=True)  # "kadın" veya "erkek" — TTS ses seçimi ve avatar için
    age_at_reference = Column(Integer, nullable=True)

    # 5 boyut, her biri ayrı sütun (basitlik için — alternatif olarak
    # JSON sütunu da kullanılabilirdi, ama SQLite'ta JSON sorgulamak
    # daha zor olduğu için düz sütunlar tercih edildi).
    emotional_patterns = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)
    life_preferences = Column(Text, nullable=True)
    decision_making_traits = Column(Text, nullable=True)
    relationship_dynamics = Column(Text, nullable=True)

    # AHP'den (bu persona'nın KENDİ ikili karşılaştırmalarından) hesaplanan
    # kişiye özel ağırlıklar.
    weight_emotional_patterns = Column(Float, nullable=True)
    weight_communication_style = Column(Float, nullable=True)
    weight_life_preferences = Column(Float, nullable=True)
    weight_decision_making_traits = Column(Float, nullable=True)
    weight_relationship_dynamics = Column(Float, nullable=True)

    # AHP tutarlılık oranı (CR) — 0.10'un altında olması beklenir.
    consistency_ratio = Column(Float, nullable=True)

    # Ham ikili karşılaştırmaların JSON hali — düzenleme sırasında
    # kaydırıcıları kaldığı yerden göstermek için saklanır.
    comparisons_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
