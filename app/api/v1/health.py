from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.chat import HealthResponse

router = APIRouter(tags=["Health Check"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check Endpoint",
    description="Check the operational status of Minni API and Gemini configuration."
)
async def health_check() -> HealthResponse:
    """Returns status, service name, version, timestamp, and Gemini configuration state."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        gemini_configured=settings.is_gemini_configured(),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

