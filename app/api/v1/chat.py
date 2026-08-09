import re
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.safety_service import safety_service
from app.services.session_service import session_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger("minni.api.chat")
router = APIRouter(tags=["Chatbot"])


def strip_wake_word(message: str) -> str:
    """Strips leading wake words ('Hey Minni', 'Hi Minni', 'Hello Minni', 'OK Minni', 'Minni,') from transcribed robot hardware speech."""
    cleaned = message.strip()
    cleaned = re.sub(r"^(hey|hi|hello|ok)\s+minni[,!\s]*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^minni[,!\s]+", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else message.strip()


def clean_voice_text(text: str) -> str:
    """Removes markdown formatting characters to produce a clean plain-text string for robot hardware Text-to-Speech (TTS) engines."""
    clean = re.sub(r"\*+", "", text)
    clean = re.sub(r"#+\s*", "", clean)
    clean = re.sub(r"`+", "", clean)
    clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)
    clean = re.sub(r"\n+", " ", clean)
    return clean.strip()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Minni ChatGPT-Style Text/Speech Endpoint for Hardware",
    description=(
        "Main API endpoint for robot hardware.\n\n"
        "- Receives input transcribed from robot microphone after wake-word 'Hey Minni' is detected.\n"
        "- Automatically cleans leading wake words ('Hey Minni', 'Hi Minni').\n"
        "- Evaluates input through Safety Layer and generates ChatGPT-style conversational responses.\n"
        "- Returns `response` (formatted text) and `voice_text` (clean plain-text for robot TTS speakers)."
    )
)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Processes user text input from robot microphone and generates ChatGPT-style Minni safety response."""
    try:
        raw_message = payload.message.strip()
        user_message = strip_wake_word(raw_message)
        audience = payload.audience or "general"

        session_id = session_service.get_or_create_session_id(payload.session_id)

        intent, risk_level, flagged, emergency_response = safety_service.analyze_message(
            user_message, audience=audience
        )

        if risk_level == "HIGH_RISK" and emergency_response:
            action_taken = "predefined_emergency_override"
            response_text = emergency_response
            voice_txt = clean_voice_text(response_text)
            helpline_info = safety_service.HELPLINE_SUMMARY

            logger.warning(f"High risk trigger detected in session {session_id} [Intent: {intent}]")
            session_service.add_turn(session_id, user_message, response_text)

            return ChatResponse(
                response=response_text,
                voice_text=voice_txt,
                session_id=session_id,
                intent=intent,
                risk_level=risk_level,
                flagged=flagged,
                action_taken=action_taken,
                helpline_info=helpline_info
            )

        session_history = session_service.get_history(session_id)
        
        response_text = gemini_service.generate_response(
            message=user_message,
            intent=intent,
            session_history=session_history,
            audience=audience
        )

        voice_txt = clean_voice_text(response_text)

        session_service.add_turn(session_id, user_message, response_text)

        return ChatResponse(
            response=response_text,
            voice_text=voice_txt,
            session_id=session_id,
            intent=intent,
            risk_level=risk_level,
            flagged=flagged,
            action_taken="normal_response",
            helpline_info=None
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request."
        )


@router.post(
    "/chat/voice",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Minni Hardware Audio Recording Endpoint",
    description="Accepts an audio file upload (.wav, .mp3, .ogg, .webm, .m4a) recorded directly from hardware microphone, processes it natively through Gemini multimodal AI, and returns Minni's response."
)
async def chat_voice_endpoint(
    audio_file: UploadFile = File(..., description="Audio file recording from hardware microphone (.wav, .mp3, .ogg, .webm, .m4a)"),
    session_id: Optional[str] = Form(None, description="Optional session ID"),
    audience: Optional[str] = Form("general", description="Target audience: 'child', 'woman', or 'general'")
) -> ChatResponse:
    """Processes uploaded hardware microphone audio file directly and generates ChatGPT-style Minni response."""
    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file uploaded from hardware."
            )

        mime_type = audio_file.content_type or "audio/wav"
        sid = session_service.get_or_create_session_id(session_id)
        aud = audience or "general"

        session_history = session_service.get_history(sid)

        response_text = gemini_service.generate_response_from_audio(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            session_history=session_history,
            audience=aud
        )

        voice_txt = clean_voice_text(response_text)

        session_service.add_turn(sid, "[Hardware Voice Audio Input]", response_text)

        return ChatResponse(
            response=response_text,
            voice_text=voice_txt,
            session_id=sid,
            intent="voice_audio_input",
            risk_level="SAFE",
            flagged=False,
            action_taken="multimodal_audio_response",
            helpline_info=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the hardware audio input."
        )


@router.delete(
    "/chat/session/{session_id}",
    summary="Clear Chat Session History",
    description="Deletes conversation context history for the given session_id."
)
async def clear_session(session_id: str):
    """Deletes conversation context history for a given session ID."""
    success = session_service.clear_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or already empty."
        )
    return {"message": f"Session '{session_id}' history cleared successfully."}
