"""
STT endpoint — accepts a recorded audio file (from the browser's
microphone) and returns the transcribed text.
"""
import os
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.stt import transcribe_audio

router = APIRouter()


@router.post("/")
async def speech_to_text(audio: UploadFile = File(...)):
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")

    # Save the uploaded audio to a temp file with a unique name (concurrent
    # requests must not overwrite each other's file).
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    temp_path = os.path.join(tempfile.gettempdir(), f"bdte_stt_{uuid.uuid4().hex}{suffix}")

    try:
        contents = await audio.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        text = transcribe_audio(temp_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"STT error: {exc}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {"text": text}
