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
    age_at_reference = Column(Integer, nullable=True)

    emotional_patterns = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)
    life_preferences = Column(Text, nullable=True)
    decision_making_traits = Column(Text, nullable=True)
    relationship_dynamics = Column(Text, nullable=True)

    weight_emotional_patterns = Column(Float, nullable=True)
    weight_communication_style = Column(Float, nullable=True)
    weight_life_preferences = Column(Float, nullable=True)
    weight_decision_making_traits = Column(Float, nullable=True)
    weight_relationship_dynamics = Column(Float, nullable=True)

    consistency_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)