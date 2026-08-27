"""
TTS (Text-to-Speech) module — uses Coqui TTS (XTTS-v2) for spoken replies.

NOTE: uses the "coqui-tts" package (idiap fork) — the original "TTS"
package is no longer maintained (Coqui AI the company shut down in 2024,
and the original package stayed limited to Python <3.11). This project
uses Python 3.11, so either would technically work, but the maintained
fork was chosen.

The XTTS-v2 model is released under the Coqui Public Model License (CPML)
— suitable for academic/non-commercial use (see https://coqui.ai/cpml.txt).
This is fine for a non-commercial capstone project, but the license note
is worth mentioning in the report.

The model is downloaded from Hugging Face on first call (~2GB) — this can
take a few minutes and requires an internet connection. Subsequent calls
are much faster since the model stays in memory/on disk.
"""
import threading

_tts_instance = None
_lock = threading.Lock()

# One of the model's built-in speakers is picked based on gender — no
# reference audio (speaker_wav) needs to be recorded.
# TODO (future work): a short reference-audio voice cloning (speaker_wav)
# matched to the persona's age/voice could personalize this further.
GENDER_SPEAKER_MAP = {
    "female": "Ana Florence",
    "male": "Craig Gutsy",
}
DEFAULT_SPEAKER = GENDER_SPEAKER_MAP["female"]


def _get_tts():
    """
    Loads the TTS model only once (on first call) and keeps it in memory
    (lazy singleton). Model loading is heavy, so we don't want to reload
    it on every request.
    """
    global _tts_instance
    if _tts_instance is None:
        with _lock:
            if _tts_instance is None:  # double-checked locking
                import torch
                from TTS.api import TTS

                gpu = torch.cuda.is_available()
                _tts_instance = TTS(
                    "tts_models/multilingual/multi-dataset/xtts_v2", gpu=gpu
                )
    return _tts_instance


def synthesize_speech(
    text: str, output_path: str, language: str = "en", gender: str | None = None
) -> str:
    """
    Converts text to speech, writes it to a wav file, returns the file path.
    If gender is given ("female"/"male"), the matching voice is used.
    """
    tts = _get_tts()
    speaker = GENDER_SPEAKER_MAP.get(gender, DEFAULT_SPEAKER)
    tts.tts_to_file(
        text=text,
        speaker=speaker,
        language=language,
        file_path=output_path,
    )
    return output_path
