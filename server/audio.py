"""Voice notes -> text. One Whisper model per process, CPU int8."""

import io
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
MAX_AUDIO = 25 * 1024 * 1024
MAX_MINUTES = 10

_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe(data: bytes) -> dict:
    """Return {text, language, duration}. Raises ValueError for too big or too long."""
    if len(data) > MAX_AUDIO:
        raise ValueError("Voice note 25 MB se badi hai")
    segments, info = model().transcribe(io.BytesIO(data), vad_filter=True)
    if info.duration > MAX_MINUTES * 60:
        raise ValueError("Voice note 10 minute se lambi hai")
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return {"text": text, "language": info.language, "duration": round(info.duration, 1)}
