import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    description=(
        "### Minni - AI Safety Assistant for Children & Women 🌸\n\n"
        "Minni is a friendly, supportive AI safety companion API powered by Google Gemini.\n\n"
        "**Key Features:**\n"
        "- 🛡️ **Safety & Intent Classification**: Pre-evaluates messages for risk levels.\n"
        "- 🚨 **High-Risk Emergency Interception**: Immediate predefined safe responses with helpline numbers (1098 Childline, 181 Women Helpline, 112/911 Emergency).\n"
        "- 🤖 **Gemini AI Integration**: Natural, warm, age-appropriate guidance for body safety, stranger safety, bullying, and online privacy.\n"
        "- 💬 **Session Context**: Contextual multi-turn chat support using `session_id`.\n"
        "- 🤖 **Robot API Ready**: Clean, lightweight REST interface (`POST /api/chat`) for speech-to-text / text-to-speech robot integration."
    ),
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

# Mount static files directory if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Register API Router (/api/chat, /api/health)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the Minni Web Chat Frontend UI."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "chat_endpoint": "/api/chat"
    }

