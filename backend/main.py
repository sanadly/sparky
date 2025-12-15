from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import asyncio
import os
import redis
import json
# Import refactored modules
from .config import settings
from .logger import setup_logging
from .services.llm_service import llm_service
from .schemas import UserMessage, PitchRequest
from .session_manager import session_manager
from .services.chat_service import chat_service, email_service

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(session_manager.cleanup_loop())
    # Email polling is now handled by a separate worker (backend/email_worker.py)
    yield

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (can be restricted in prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
if os.path.exists("web-portal/dist"):
    app.mount("/assets", StaticFiles(directory="web-portal/dist/assets"), name="assets")
    @app.get("/")
    async def read_index():
        return FileResponse('web-portal/dist/index.html')
else:
    app.mount("/static", StaticFiles(directory="."), name="static")
    @app.get("/")
    async def read_index():
        return FileResponse('index.html')

@app.post("/api/chat")
async def chat_endpoint(msg: UserMessage):
    logger.info(f"Received message from {msg.user_id}: {msg.message}")
    response = await chat_service.handle_message(msg.user_id, msg.message)
    
    # Ensure all keys are present for frontend
    current_session = await session_manager.get_session(msg.user_id)
    return {
        "reply": response.get("reply"),
        "state": response.get("state", current_session["state"]),
        "ui_data": response.get("ui_data")
    }

# Pitch Cache to speed up demo
# Redis Connection
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    redis_client = None

# Initial Cache Population (if Redis is empty)
INITIAL_PITCHES = {
    "INTENSIVE 12 Demo-Produkt": "Der **INTENSIVE 12** Mix-Tarif bietet dir 12 Monate Top-Sicherheit und einen ausgewogenen Energiemix!",
    "INTENSIVE 24 Demo-Produkt": "Hey! Der **INTENSIVE 24 Mix** bietet dir maximale **Planungssicherheit** und faire Konditionen für zwei Jahre. ⚡",
    "INTENSIVE Day & Night Demo-Produkt": "**Tag- und Nachtstrom** intelligent kombiniert für dich! ⚡ Das gibt dir maximale **Flexibilität**.",
    "INTENSIVE Day & Night Demo-Produkt 24": "**Tag & Nacht** sparen: Der perfekte Mix für deinen Bedarf! ⚡"
}

if redis_client:
    try:
        for key, value in INITIAL_PITCHES.items():
            if not redis_client.exists(f"pitch:{key}"):
                redis_client.set(f"pitch:{key}", value)
    except Exception as e:
        logger.error(f"Failed to populate Redis cache: {e}")

@app.post("/api/pitch")
async def pitch_endpoint(req: PitchRequest):
    try:
        # Check Redis Cache
        cache_key = f"pitch:{req.product_name}"
        if redis_client:
            cached_pitch = redis_client.get(cache_key)
            if cached_pitch:
                return {"pitch": cached_pitch}
            
        if req.consumption == 0:
            prompt = f"Produkt: {req.product_name}, Typ: {'Öko' if req.is_green else 'Mix'}. Schreibe einen kurzen, werblichen Satz (max 10 Wörter), warum dieser Tarif toll ist (z.B. 'Perfekt für maximale Flexibilität'). Erwähne KEINEN Verbrauch."
        else:
            prompt = f"Produkt: {req.product_name}, Typ: {'Öko' if req.is_green else 'Mix'}, Verbrauch: {req.consumption}. Ein kurzer, peppiger Satz warum das passt."
        
        pitch = llm_service.generate_answer(prompt)
        
        # Cache the result
        if redis_client:
            redis_client.set(cache_key, pitch, ex=3600*24) # Cache for 24 hours
        
        return {"pitch": pitch}
    except Exception as e:
        logger.error(f"Pitch generation failed: {e}")
        return {"pitch": "Ein ausgezeichneter Tarif für dich."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
