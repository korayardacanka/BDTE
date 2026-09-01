"""
BDTE (Behavioral Digital Twin for Elderly) — Backend API
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.persona import seed_default_persona
from app.routers import health, profile, chat, tts, stt

settings = get_settings()

app = FastAPI(
    title="BDTE API",
    description="Behavioral Digital Twin for Elderly — backend service",
    version="0.1.0",
)

# Create database tables (if they don't exist yet) on startup.
init_db()

# Insert an example/synthetic persona if the database is empty (first-run convenience).
_seed_db = SessionLocal()
try:
    seed_default_persona(_seed_db)
finally:
    _seed_db.close()

# Allow the frontend (localhost:5173) to reach the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(tts.router, prefix="/api/tts", tags=["tts"])
app.include_router(stt.router, prefix="/api/stt", tags=["stt"])

@app.get("/")
def root():
    return {"service": "bdte-backend", "status": "running", "version": app.version}
