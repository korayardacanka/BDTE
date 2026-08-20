"""
Diyalog endpoint'i.

Artık Ollama'nın /api/chat endpoint'ini kullanıyor (mesaj geçmişi + system
prompt destekli). Persona.py'deki davranışsal profil, her konuşmanın
başında bir "system" mesajı olarak modele veriliyor — bu, "prompt
engineering" ile davranışsal temellendirme (behavioral grounding) yaklaşımının
temelini oluşturuyor.

TODO (ileride, veri/gerçek profil geldiğinde):
- persona.py yerine veritabanından (behavioral_profile tablosu) okuma
- pgvector ile geçmiş konuşmalardan ilgili anıları getirme (tam RAG)
"""
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.persona import EXAMPLE_PERSONA, build_system_prompt

router = APIRouter()
settings = get_settings()

# Basit, bellek-içi (in-memory) konuşma geçmişi.
# Not: Backend yeniden başladığında (--reload) veya birden fazla worker
# process çalıştığında bu sıfırlanır/tutarsız olur. Kalıcı hale getirmek
# (PostgreSQL'e yazmak) bir sonraki adım.
_conversations: dict[str, list[dict]] = {}

SYSTEM_PROMPT = build_system_prompt(EXAMPLE_PERSONA)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None


@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    session_id = req.session_id or "default"
    history = _conversations.setdefault(session_id, [])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": req.message}
    ]

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,  # çok yüksek olursa dil karışması/tutarsızlık artar
                    },
                },
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "").strip()
    except Exception as exc:  # Ollama henüz kurulu/çalışır değilse
        reply = f"[LLM henüz bağlı değil — stub yanıt] Mesajını aldım: '{req.message}' ({exc.__class__.__name__})"
        return ChatResponse(reply=reply, session_id=session_id)

    # Geçmişe ekle (sadece user+assistant, system her seferinde ayrıca ekleniyor)
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    # Geçmişi çok uzamasın diye son 20 mesajla sınırla (basit bir önlem)
    _conversations[session_id] = history[-20:]

    return ChatResponse(reply=reply, session_id=session_id)