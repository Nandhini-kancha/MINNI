import re
import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.safety_service import safety_service
from app.services.session_service import session_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger("minni.api.chat")
router = APIRouter(tags=["Chatbot"])


def strip_wake_word(message: str) -> str:
    """Strips leading wake words ('Hey Minni', 'Hi Minni', 'Hello Minni', 'Minni,') from user speech input."""
    cleaned = message.strip()
    # Remove 'Hey Minni', 'Hi Minni', 'Hello Minni' prefix
    cleaned = re.sub(r"^(hey|hi|hello)\s+minni[,!\s]*", "", cleaned, flags=re.IGNORECASE).strip()
    # Remove standalone 'Minni,' or 'Minni ' prefix
    cleaned = re.sub(r"^minni[,!\s]+", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else message.strip()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Minni Robot Chat Endpoint",
    description=(
        "Conversational API endpoint for Robot integration.\n\n"
        "- Expects text input transcribed from robot speech after wake word 'Hey Minni' is detected.\n"
        "- Automatically cleans leading wake words ('Hey Minni', 'Hi Minni').\n"
        "- Pre-evaluates messages through Safety & Intent classification layer.\n"
        "- High-risk inputs (abuse, self-harm, immediate danger) trigger instant pre-defined safe responses with helpline numbers.\n"
        "- Context is preserved per `session_id`."
    )
)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Processes user text from robot STT and generates Minni safety response."""
    try:
        raw_message = payload.message.strip()
        # Clean wake word if present in transcribed speech
        user_message = strip_wake_word(raw_message)
        audience = payload.audience or "general"

        # 1. Resolve or generate session ID
        session_id = session_service.get_or_create_session_id(payload.session_id)

        # 2. Run Pre-Generation Safety & Intent Classification
        intent, risk_level, flagged, emergency_response = safety_service.analyze_message(
            user_message, audience=audience
        )

        # 3. Handle High-Risk Emergency Interception
        if risk_level == "HIGH_RISK" and emergency_response:
            action_taken = "predefined_emergency_override"
            response_text = emergency_response
            helpline_info = safety_service.HELPLINE_SUMMARY

            logger.warning(f"High risk trigger detected in session {session_id} [Intent: {intent}]")

            # Save emergency turn to session history
            session_service.add_turn(session_id, user_message, response_text)

            return ChatResponse(
                response=response_text,
                session_id=session_id,
                intent=intent,
                risk_level=risk_level,
                flagged=flagged,
                action_taken=action_taken,
                helpline_info=helpline_info
            )

        # 4. Normal / Sensitive Processing via Gemini API
        session_history = session_service.get_history(session_id)
        
        response_text = gemini_service.generate_response(
            message=user_message,
            intent=intent,
            session_history=session_history,
            audience=audience
        )

        # 5. Save turn in session context
        session_service.add_turn(session_id, user_message, response_text)

        return ChatResponse(
            response=response_text,
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
            detail="An error occurred while processing your request. Please try again."
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
