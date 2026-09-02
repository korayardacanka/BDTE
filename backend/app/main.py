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
# Pre-load (warm up) the TTS model at startup, BEFORE the STT (faster-whisper)
# model can ever be loaded by a user request.
#
# Why: PyTorch (used by Coqui TTS) and ctranslate2 (used by faster-whisper for
# STT) can each bundle a different, incompatible CUDA/cuDNN runtime version.
# On Windows, whichever library's cuDNN gets loaded into the process FIRST
# "wins" and stays resident; if STT loads first, TTS later fails with an
# error like "Could not load symbol cudnnGetLibConfig". Warming up TTS here,
# before any request (including STT) can be handled, guarantees a safe load
# order regardless of which feature the user tries first in the UI.
#
# Wrapped in try/except so a TTS load failure doesn't prevent the whole
# backend from starting — TTS will just lazy-load again on first real
# request as a fallback (with the same race-condition risk as before).
try:
    from app.tts import _get_tts

    _get_tts()
    print("[startup] TTS model pre-loaded successfully.")
except Exception as exc:
    print(f"[startup] WARNING: could not pre-load TTS model ({exc}). "
          f"It will load lazily on first request instead.")
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
