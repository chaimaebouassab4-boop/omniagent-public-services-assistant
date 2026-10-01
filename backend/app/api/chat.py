from typing import Optional, List
import asyncio
import base64
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from app.services.vector_retrieval import RetrievedChunk

from app.rag_service import query_rag
from app.services.audio_service import (
    ALLOWED_AUDIO_MIMES,
    get_browser_voice_config,
    sanitize_for_voice,
    synthesize_speech,
    synthesize_speech_async,
    transcribe_audio,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# ── Existing models ────────────────────────────────────────────────────────
class RAGQueryRequest(BaseModel):
    query: str
    service_type: Optional[str] = None


class RAGQueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    language: str = "darija"
    fallback_reason: Optional[str] = None
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    backend: str = "bm25"
    threshold: float | None = None
    candidate_count: int = 0


# ── Voice models ───────────────────────────────────────────────────────────
class VoiceTranscribeResponse(BaseModel):
    text: str
    language: str
    confidence: float
    error: Optional[str] = None


class VoiceSynthesizeRequest(BaseModel):
    text: str
    language: str = "ar"


class VoiceReadyRequest(BaseModel):
    text: str
    language: str = "darija"


class VoiceReadyResponse(BaseModel):
    voiceText: str
    originalLength: int
    voiceLength: int
    browserVoiceConfig: dict


# ── Existing endpoints ─────────────────────────────────────────────────────

@router.get("/chat/ping")
def ping_chat() -> dict:
    """Health ping for chat namespace."""
    return {"status": "success", "data": {"message": "chat online"}}


@router.post("/chat/query", response_model=RAGQueryResponse)
def query_chat_rag(body: RAGQueryRequest) -> RAGQueryResponse:
    """RAG query endpoint returning grounded Darija answer with metadata."""
    res = query_rag(user_query=body.query, service_type=body.service_type)
    return RAGQueryResponse(
        answer=res.get("answer", ""),
        confidence=res.get("confidence", 0.0),
        sources=res.get("sources", []),
        language=res.get("language", "darija"),
        fallback_reason=res.get("fallback_reason"),
        chunks=res.get("chunks", []),
        backend=res.get("backend", "bm25"),
        threshold=res.get("threshold"),
        candidate_count=res.get("candidate_count", 0),
    )


# ═══════════════════════════════════════════════════════════════════════════ #
#  Task 1.1 — Voice Transcription (Speech-to-Text)
# ═══════════════════════════════════════════════════════════════════════════ #

@router.post(
    "/chat/voice-transcribe",
    response_model=VoiceTranscribeResponse,
    status_code=200,
    summary="Transcribe Darija / Arabic / French audio to text",
)
async def voice_transcribe(
    file: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    language: str = Form("darija"),
):
    """Transcribe an audio recording to text using Gemini Flash Audio.

    Accepts audio either as a multipart file upload **or** as a base64-encoded
    string (useful for browser MediaRecorder → base64 flows).

    **Supported formats:** webm, wav, mp3, ogg, m4a, aac, flac, mp4.

    **Language hints:** ``darija`` (default), ``ar``, ``fr``.
    """
    audio_bytes: bytes
    resolved_mime: str

    # ── Option A: file upload ──
    if file is not None:
        resolved_mime = file.content_type or "audio/webm"
        audio_bytes = await file.read()
    # ── Option B: base64 ──
    elif audio_base64 is not None:
        resolved_mime = mime_type or "audio/webm"
        try:
            # Strip optional data-URI prefix
            if "," in audio_base64:
                header, audio_base64 = audio_base64.split(",", 1)
                if ";" in header:
                    # e.g. data:audio/webm;base64
                    resolved_mime = header.split(":")[1].split(";")[0]
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 audio data: {exc}",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'file' (multipart upload) or 'audio_base64' (base64 string).",
        )

    # ── Validate ──
    if resolved_mime not in ALLOWED_AUDIO_MIMES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {resolved_mime}. "
                   f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_MIMES))}",
        )

    max_bytes = settings.max_audio_upload_bytes
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Audio too large ({len(audio_bytes):,} bytes). Max: {max_bytes:,} bytes.",
        )

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    # ── Transcribe ──
    result = await asyncio.to_thread(
        transcribe_audio,
        audio_bytes=audio_bytes,
        mime_type=resolved_mime,
        language_hint=language,
    )

    return VoiceTranscribeResponse(
        text=result["text"],
        language=result["language"],
        confidence=result["confidence"],
        error=result.get("error"),
    )


# ═══════════════════════════════════════════════════════════════════════════ #
#  Task 1.2 — Voice Synthesis (Text-to-Speech)
# ═══════════════════════════════════════════════════════════════════════════ #

@router.post(
    "/chat/voice-synthesize",
    status_code=200,
    summary="Synthesize text to speech (MP3 audio)",
    responses={200: {"content": {"audio/mpeg": {}}}},
)
async def voice_synthesize(body: VoiceSynthesizeRequest):
    """Convert text to spoken audio (MP3).

    Automatically sanitizes markdown before synthesis.
    Returns raw MP3 bytes with ``Content-Type: audio/mpeg``.
    """
    # Clean the text for voice first
    clean_text = sanitize_for_voice(body.text, body.language)
    if not clean_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No speakable content after sanitizing the text.",
        )

    try:
        mp3_bytes = await synthesize_speech_async(clean_text, body.language)
    except (ValueError, RuntimeError) as exc:
        logger.warning("Voice synthesis request failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(
        content=mp3_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=\"speech.mp3\"",
            "Cache-Control": "no-cache",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════ #
#  Task 1.2 — Voice-Ready Text + Browser Config
# ═══════════════════════════════════════════════════════════════════════════ #

@router.post(
    "/chat/voice-ready-text",
    response_model=VoiceReadyResponse,
    status_code=200,
    summary="Transform AI response into voice-ready text with browser config",
)
async def voice_ready_text(body: VoiceReadyRequest):
    """Strip markdown/tables from an AI response and return concise voice text.

    Also returns recommended browser ``Web Speech API`` configuration for
    ``SpeechSynthesisUtterance`` playback of Darija / Arabic / French.
    """
    clean = sanitize_for_voice(body.text, body.language)
    config = get_browser_voice_config(body.language)

    return VoiceReadyResponse(
        voiceText=clean,
        originalLength=len(body.text),
        voiceLength=len(clean),
        browserVoiceConfig=config,
    )
