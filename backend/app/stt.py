"""
STT (Speech-to-Text) module — uses faster-whisper (a CTranslate2-based,
open-source reimplementation of OpenAI's Whisper) to transcribe recorded
speech into text.

NOTE: faster-whisper is fully open-source and self-hosted, consistent with
the project's open-source technology stack (no cloud API calls). It
reports up to 4x faster inference than the original openai-whisper package
at the same accuracy.

Model size: "small" is used as a balance between accuracy and speed for
short chat-length utterances. Larger models ("medium", "large-v3") give
better accuracy but are slower and use more VRAM/RAM — can be changed
below if needed.

GPU vs CPU: GPU execution requires matching CUDA/cuDNN library versions,
which can be finicky to set up (a common source of setup friction). Since
STT here only needs to transcribe short chat messages (a few seconds of
audio), CPU with int8 quantization is fast enough and far more reliable
across different machines — so CPU is used by default. If you have a
working CUDA + cuDNN setup and want lower latency, change DEVICE to
"cuda" and COMPUTE_TYPE to "float16" below.
"""
import threading

_stt_instance = None
_lock = threading.Lock()

MODEL_SIZE = "small"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


def _get_stt():
    """Loads the Whisper model only once (lazy singleton)."""
    global _stt_instance
    if _stt_instance is None:
        with _lock:
            if _stt_instance is None:
                from faster_whisper import WhisperModel

                _stt_instance = WhisperModel(
                    MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE
                )
    return _stt_instance


def transcribe_audio(audio_path: str, language: str = "en") -> str:
    """
    Transcribes an audio file into text. Returns the transcribed text
    (empty string if nothing was recognized).
    """
    model = _get_stt()
    segments, _info = model.transcribe(audio_path, language=language, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments).strip()