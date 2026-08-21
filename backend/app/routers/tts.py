"""
TTS endpoint'i — metni sese çevirip ses dosyası (wav) olarak döner.
persona_id verilirse, o persona'nın cinsiyetine uygun ses kullanılır.
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
    language: str = "tr"
    persona_id: int | None = None


@router.post("/")
def text_to_speech(req: TTSRequest, db: Session = Depends(get_db)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text boş olamaz")

    gender = None
    if req.persona_id is not None:
        profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == req.persona_id).first()
        if profile:
            gender = profile.gender

    output_path = os.path.join(tempfile.gettempdir(), "bdte_tts_output.wav")
    try:
        synthesize_speech(req.text, output_path=output_path, language=req.language, gender=gender)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS hatası: {exc}")

    return FileResponse(output_path, media_type="audio/wav", filename="response.wav")