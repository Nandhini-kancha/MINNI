from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request payload for the POST /api/chat endpoint."""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="The text prompt or question transcribed from hardware microphone.",
        examples=["Hey Minni, explain about safe touch"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to maintain conversation context across multiple hardware interactions.",
        examples=["robot-session-12345"]
    )
    audience: Optional[str] = Field(
        default="general",
        description="Target audience type: 'child', 'woman', or 'general'.",
        examples=["child"]
    )


class ChatResponse(BaseModel):
    """Response payload for the POST /api/chat and POST /api/chat/voice endpoints."""
    response: str = Field(..., description="Minni's ChatGPT-style natural conversational response text (with markdown).")
    voice_text: str = Field(..., description="Clean, voice-optimized plain text formatted specifically for robot hardware Text-to-Speech (TTS) engines.")
    session_id: str = Field(..., description="Active session ID for hardware conversation tracking.")
    intent: str = Field(..., description="Detected user intent category.")
    risk_level: str = Field(..., description="Assessed risk level: SAFE, SENSITIVE, or HIGH_RISK.")
    flagged: bool = Field(..., description="True if a safety risk or emergency override was triggered.")
    action_taken: str = Field(..., description="Action taken: normal_response or predefined_emergency_override.")
    helpline_info: Optional[str] = Field(default=None, description="Helpline numbers if high-risk situation detected.")


class HealthResponse(BaseModel):
    """Response payload for the GET /api/health endpoint."""
    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["Minni AI Safety Assistant"])
    version: str = Field(..., examples=["1.0.0"])
    gemini_configured: bool = Field(..., description="True if GEMINI_API_KEY is validly configured.")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp.")
