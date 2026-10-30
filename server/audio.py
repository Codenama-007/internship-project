"""Voice notes -> text via Groq's hosted Whisper, so the server needs no model or ffmpeg."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MAX_AUDIO = 25 * 1024 * 1024
MAX_MINUTES = 10


def transcribe(data: bytes, filename: str = "voice.webm") -> dict:
    """Return {text, language, duration}. Raises ValueError for too big or too long."""
    if len(data) > MAX_AUDIO:
        raise ValueError("Voice note 25 MB se badi hai")
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    response = httpx.post(
        URL,
        headers={"Authorization": f"Bearer {key}"},
        files={"file": (filename, data)},
        data={"model": MODEL, "response_format": "verbose_json"},
        timeout=120,
    )
    if response.status_code >= 400:
        print(f"[voice] groq {response.status_code}", flush=True)
        raise RuntimeError("transcription failed")
    body = response.json()
    duration = float(body.get("duration") or 0)
    if duration > MAX_MINUTES * 60:
        raise ValueError("Voice note 10 minute se lambi hai")
    return {
        "text": (body.get("text") or "").strip(),
        "language": body.get("language"),
        "duration": round(duration, 1),
    }
