"""
SQLAlchemy models (database tables).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class ConversationMessage(Base):
    """Persists every chat message (user and assistant) permanently."""

    __tablename__ = "conversation_log"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BehavioralProfile(Base):
    """
    Behavioral profile record. Each persona has its own CUSTOM weights,
    computed from its own pairwise comparisons (AHP) — no fixed/shared
    weights are used. This is the core of the project's MCDM methodology.
    """

    __tablename__ = "behavioral_profile"

    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(128), nullable=False)
    relation = Column(String(64), nullable=True)
    gender = Column(String(16), nullable=True)  # "female" or "male" — used for TTS voice + avatar
    age_at_reference = Column(Integer, nullable=True)

    # 5 dimensions, one column each (kept simple — a JSON column would be
    # an alternative, but plain columns are easier to query in SQLite).
    emotional_patterns = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)
    life_preferences = Column(Text, nullable=True)
    decision_making_traits = Column(Text, nullable=True)
    relationship_dynamics = Column(Text, nullable=True)

    # Custom weights computed via AHP from this persona's OWN pairwise
    # comparisons.
    weight_emotional_patterns = Column(Float, nullable=True)
    weight_communication_style = Column(Float, nullable=True)
    weight_life_preferences = Column(Float, nullable=True)
    weight_decision_making_traits = Column(Float, nullable=True)
    weight_relationship_dynamics = Column(Float, nullable=True)

    # AHP consistency ratio (CR) — expected to be below 0.10.
    consistency_ratio = Column(Float, nullable=True)

    # Raw pairwise comparisons as JSON — kept so the slider positions can
    # be restored exactly when editing a persona later.
    comparisons_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
