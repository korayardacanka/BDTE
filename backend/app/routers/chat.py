"""
Diyalog endpoint'i.

Ollama'nın /api/chat endpoint'ini kullanır (mesaj geçmişi + system prompt
destekli). Persona.py'deki davranışsal profil, her konuşmanın başında bir
"system" mesajı olarak modele veriliyor.

Konuşma geçmişi artık SQLite'a (conversation_log tablosu) kalıcı olarak
yazılıyor — backend yeniden başlasa bile geçmiş kaybolmuyor.

TODO (ileride, veri/gerçek profil geldiğinde):
- persona.py yerine veritabanından (behavioral_profile tablosu) okuma
- pgvector ile geçmiş konuşmalardan ilgili anıları getirme (tam RAG)
"""
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ConversationMessage
from app.persona import EXAMPLE_PERSONA, build_system_prompt

router = APIRouter()
settings = get_settings()

SYSTEM_PROMPT = build_system_prompt(EXAMPLE_PERSONA)

MAX_HISTORY_MESSAGES = 20  # LLM'e gönderilecek son N mesajla sınırla


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None


def _load_history(db: Session, session_id: str) -> list[dict]:
    """Veritabanından, bu session'a ait son mesajları okur."""
    rows = (
        db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.id.desc())
            .limit(MAX_HISTORY_MESSAGES)
        )
        .scalars()
        .all()
    )
    rows = list(reversed(rows))
    return [{"role": r.role, "content": r.content} for r in rows]


def _save_message(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(ConversationMessage(session_id=session_id, role=role, content=content))
    db.commit()


@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    session_id = req.session_id or "default"
    history = _load_history(db, session_id)

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
                        "temperature": 0.6,
                    },
                },
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "").strip()
    except Exception as exc:
        reply = f"[LLM henüz bağlı değil — stub yanıt] Mesajını aldım: '{req.message}' ({exc.__class__.__name__})"
        return ChatResponse(reply=reply, session_id=session_id)

    _save_message(db, session_id, "user", req.message)
    _save_message(db, session_id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=session_id)