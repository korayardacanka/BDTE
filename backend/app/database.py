"""
Database connection (SQLite — for local development).

NOTE (scope decision): The original plan used PostgreSQL + pgvector for
real RAG (embedding-based search). Right now the persona is injected as a
fixed "system prompt" (no embedding search), so SQLite is sufficient and
requires zero extra setup on native Windows.

If real RAG is added later: just point DATABASE_URL at a PostgreSQL+pgvector
address — the SQLAlchemy models (models.py) keep working unchanged.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite needs "check_same_thread=False" because FastAPI may handle
# requests on different threads.
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — opens a DB session per request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates tables if they don't exist yet. Called once on app startup."""
    Base.metadata.create_all(bind=engine)
