"""
BDTE (Behavioral Digital Twin for Elderly) — Backend API
FastAPI ana uygulama giriş noktası.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, profile, chat

settings = get_settings()

app = FastAPI(
    title="BDTE API",
    description="Behavioral Digital Twin for Elderly — backend service",
    version="0.1.0",
)

# Geliştirme aşamasında frontend'in (localhost:5173) API'ye erişebilmesi için CORS
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


@app.get("/")
def root():
    return {"service": "bdte-backend", "status": "running", "version": app.version}
