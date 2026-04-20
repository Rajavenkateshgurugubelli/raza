"""
Voice I/O pipeline for R.A.Z.A.
- STT: faster-whisper (local, runs on CPU, tiny model for speed)
- TTS: edge-tts (Microsoft Azure neural voices, streams MP3)

Endpoints:
  POST /api/voice/transcribe  — upload audio file → returns { "text": "..." }
  GET  /api/voice/speak       — ?text=... → streams MP3 audio
  GET  /api/voice/voices      — list available edge-tts voices
"""
import io
import logging
import tempfile
import os
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Lazy Whisper model ────────────────────────────────────────────────────────

_whisper_model = None
_whisper_loading = False


def _get_whisper():
    global _whisper_model, _whisper_loading
    if _whisper_model is not None:
        return _whisper_model
    if _whisper_loading:
        raise RuntimeError("Whisper model is still loading — try again in a moment.")
    _whisper_loading = True
    try:
        from faster_whisper import WhisperModel
        logger.info("[Voice] Loading Whisper tiny model (first-time download may take a minute)…")
        # tiny model, CPU, int8 quantization for speed
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("[Voice] Whisper model ready.")
        return _whisper_model
    except Exception as e:
        _whisper_loading = False
        raise RuntimeError(f"Failed to load Whisper: {e}") from e
    finally:
        _whisper_loading = False


# ── STT endpoint ──────────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe an uploaded audio file (webm, wav, mp3, ogg, m4a).
    Returns { "text": "...", "language": "...", "duration_s": float }
    """
    SUPPORTED = {".webm", ".wav", ".mp3", ".ogg", ".m4a", ".flac"}
    suffix = Path(file.filename or "audio.webm").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(400, f"Unsupported format '{suffix}'. Supported: {', '.join(SUPPORTED)}")

    # Write to temp file (faster-whisper needs a file path, not a stream)
    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25 MB limit
        raise HTTPException(413, "Audio file too large (max 25 MB).")

    try:
        model = _get_whisper()
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(tmp_path, beam_size=1, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return JSONResponse({
            "text": text,
            "language": info.language,
            "duration_s": round(info.duration, 2),
        })
    except Exception as e:
        logger.error(f"[Voice] Transcription failed: {e}")
        raise HTTPException(500, f"Transcription failed: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ── TTS endpoint ──────────────────────────────────────────────────────────────

DEFAULT_VOICE = "en-US-GuyNeural"   # male voice — change in .env via VOICE_TTS_VOICE
MAX_TTS_CHARS = 3000


@router.get("/speak")
async def speak_text(
    text: str = Query(..., min_length=1),
    voice: str = Query(DEFAULT_VOICE),
):
    """
    Stream MP3 audio of the given text using edge-tts.
    The audio is streamed chunk-by-chunk so playback can start immediately.
    """
    if len(text) > MAX_TTS_CHARS:
        text = text[:MAX_TTS_CHARS] + "…"

    try:
        import edge_tts
        communicate = edge_tts.Communicate(text=text, voice=voice)

        async def audio_generator():
            try:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        yield chunk["data"]
            except Exception as e:
                logger.error(f"[Voice] TTS stream error: {e}")

        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "X-Voice": voice,
            },
        )
    except ImportError:
        raise HTTPException(503, "edge-tts not installed. Run: pip install edge-tts")
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {e}")


# ── Voice list endpoint ───────────────────────────────────────────────────────

@router.get("/voices")
async def list_voices(locale: str = Query("en-US")):
    """List available edge-tts voices for a given locale."""
    try:
        import edge_tts
        all_voices = await edge_tts.list_voices()
        filtered = [
            {"name": v["Name"], "gender": v["Gender"], "locale": v["Locale"]}
            for v in all_voices
            if v["Locale"].startswith(locale)
        ]
        return filtered
    except ImportError:
        raise HTTPException(503, "edge-tts not installed.")
    except Exception as e:
        raise HTTPException(500, str(e))
