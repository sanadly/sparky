from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import asyncio
import os

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

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(session_manager.cleanup_loop())
    asyncio.create_task(email_service.run_email_polling(chat_service))
    yield

app = FastAPI(lifespan=lifespan)

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
    return {
        "reply": response.get("reply"),
        "state": response.get("state", session_manager.get_session(msg.user_id)["state"]),
        "ui_data": response.get("ui_data")
    }

# Pitch Cache to speed up demo
PITCH_CACHE = {
    "INTENSIVE 12 Demo-Produkt": "Der **INTENSIVE 12** Mix-Tarif bietet dir 12 Monate Top-Sicherheit und einen ausgewogenen Energiemix!",
    "INTENSIVE 24 Demo-Produkt": "Hey! Der **INTENSIVE 24 Mix** bietet dir maximale **Planungssicherheit** und faire Konditionen für zwei Jahre. ⚡",
    "INTENSIVE Day & Night Demo-Produkt": "**Tag- und Nachtstrom** intelligent kombiniert für dich! ⚡ Das gibt dir maximale **Flexibilität**.",
    "INTENSIVE Day & Night Demo-Produkt 24": "**Tag & Nacht** sparen: Der perfekte Mix für deinen Bedarf! ⚡"
}

@app.post("/api/pitch")
async def pitch_endpoint(req: PitchRequest):
    try:
        # Check Cache first
        if req.product_name in PITCH_CACHE:
            return {"pitch": PITCH_CACHE[req.product_name]}
            
        if req.consumption == 0:
            prompt = f"Produkt: {req.product_name}, Typ: {'Öko' if req.is_green else 'Mix'}. Schreibe einen kurzen, werblichen Satz (max 10 Wörter), warum dieser Tarif toll ist (z.B. 'Perfekt für maximale Flexibilität'). Erwähne KEINEN Verbrauch."
        else:
            prompt = f"Produkt: {req.product_name}, Typ: {'Öko' if req.is_green else 'Mix'}, Verbrauch: {req.consumption}. Ein kurzer, peppiger Satz warum das passt."
        
        pitch = llm_service.generate_answer(prompt)
        
        # Cache the result for this session/run
        PITCH_CACHE[req.product_name] = pitch
        
        return {"pitch": pitch}
    except Exception as e:
        logger.error(f"Pitch generation failed: {e}")
        return {"pitch": "Ein ausgezeichneter Tarif für dich."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
