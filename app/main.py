import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("minni")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Minni AI Safety Assistant API backend.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for robot integrations / client calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router (/api/chat, /api/chat/voice, /api/health)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect / welcome API status."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "chat_endpoint": "/api/chat",
        "voice_chat_endpoint": "/api/chat/voice"
    }
