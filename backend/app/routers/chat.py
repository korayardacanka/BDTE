"""
Diyalog endpoint iskeleti.
Hafta 1'de sadece echo/stub — Hafta 6+'da Ollama (LLM) + RAG (pgvector)
entegrasyonu ile gerçek davranışsal-temelli yanıt üretimine dönüşecek.
"""
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None


@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    """
    Şu an için Ollama'nın canlı olup olmadığını kontrol edip ham bir yanıt döner.
    TODO (Hafta 6-9): RAG ile davranışsal profili sisteme prompt olarak enjekte et,
    context-aware (episodic) yanıt mekanizmasını ekle.
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": req.message,
                    "stream": False,
                },
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("response", "").strip()
    except Exception as exc:  # Ollama henüz kurulu/çalışır değilse
        reply = f"[LLM henüz bağlı değil — stub yanıt] Mesajını aldım: '{req.message}' ({exc.__class__.__name__})"

    return ChatResponse(reply=reply, session_id=req.session_id)
