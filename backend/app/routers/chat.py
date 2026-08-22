"""
Diyalog endpoint'i.

Artık persona_id parametresi ile hangi persona'nın kullanılacağı seçilir.
Belirtilmezse, veritabanındaki ilk (varsayılan) persona kullanılır.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import BehavioralProfile, ConversationMessage
from app.persona import build_system_prompt, profile_row_to_dict

router = APIRouter()
settings = get_settings()

MAX_HISTORY_MESSAGES = 20


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    persona_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None
    persona_id: int


def _load_history(db: Session, session_id: str) -> list[dict]:
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


def _get_persona(db: Session, persona_id: int | None) -> BehavioralProfile:
    query = db.query(BehavioralProfile)
    profile = (
        query.filter(BehavioralProfile.id == persona_id).first()
        if persona_id is not None
        else query.order_by(BehavioralProfile.id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Persona bulunamadı. Önce bir persona oluşturun.")
    return profile


@router.post("/", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message boş olamaz")
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="message çok uzun (maks. 2000 karakter)")

    profile = _get_persona(db, req.persona_id)
    persona_dict = profile_row_to_dict(profile)
    system_prompt = build_system_prompt(persona_dict)

    # persona bazında ayrı konuşma geçmişi tutmak için session_id'yi
    # persona_id ile birleştiriyoruz (aynı kullanıcı farklı personalarla
    # ayrı ayrı sohbet edebilsin).
    session_id = f"{req.session_id or 'default'}::persona{profile.id}"
    history = _load_history(db, session_id)

    messages = [{"role": "system", "content": system_prompt}] + history + [
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
                    "options": {"temperature": 0.6},
                },
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "").strip()
    except Exception as exc:
        reply = f"[LLM henüz bağlı değil — stub yanıt] Mesajını aldım: '{req.message}' ({exc.__class__.__name__})"
        return ChatResponse(reply=reply, session_id=req.session_id, persona_id=profile.id)

    _save_message(db, session_id, "user", req.message)
    _save_message(db, session_id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=req.session_id, persona_id=profile.id)