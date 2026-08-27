"""
TTS endpoint — converts text to speech and returns an audio file (wav).
If persona_id is given, the persona's gender determines the voice used.
"""
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BehavioralProfile
from app.tts import synthesize_speech

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    persona_id: int | None = None


@router.post("/")
def text_to_speech(req: TTSRequest, db: Session = Depends(get_db)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    gender = None
    if req.persona_id is not None:
        profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == req.persona_id).first()
        if profile:
            gender = profile.gender

    output_path = os.path.join(tempfile.gettempdir(), "bdte_tts_output.wav")
    try:
        synthesize_speech(req.text, output_path=output_path, language=req.language, gender=gender)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS error: {exc}")

    return FileResponse(output_path, media_type="audio/wav", filename="response.wav")
