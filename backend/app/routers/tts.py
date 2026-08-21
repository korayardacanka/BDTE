"""
TTS endpoint'i — metni sese çevirip ses dosyası (wav) olarak döner.
"""
import os
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.tts import synthesize_speech

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    language: str = "tr"


@router.post("/")
def text_to_speech(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text boş olamaz")

    output_path = os.path.join(tempfile.gettempdir(), "bdte_tts_output.wav")
    try:
        synthesize_speech(req.text, output_path=output_path, language=req.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS hatası: {exc}")

    return FileResponse(output_path, media_type="audio/wav", filename="response.wav")