import time
import logging
import asyncio
import json
import redis.asyncio as redis
from .config import settings

logger = logging.getLogger(__name__)

# Constants for States
STATE_START = "START"
STATE_WAITING_FOR_CONSUMPTION = "WAITING_FOR_CONSUMPTION"
STATE_WAITING_FOR_PRODUCT_CHOICE = "WAITING_FOR_PRODUCT_CHOICE"
STATE_SIMULATION_DONE = "SIMULATION_DONE"
STATE_WAITING_FOR_DATE = "WAITING_FOR_DATE"
STATE_OFFER_CREATED = "OFFER_CREATED"
STATE_WAITING_FOR_DURATION = "WAITING_FOR_DURATION"
STATE_WAITING_FOR_TARIFF_TYPE = "WAITING_FOR_TARIFF_TYPE"
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

class SessionManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Fallback in-memory for tests or if redis fails (optional, but good for dev)
        self.local_sessions = {}

    async def get_session(self, user_id):
        try:
            data = await self.redis.get(f"session:{user_id}")
            if data:
                session = json.loads(data)
                session["last_activity"] = time.time()
                return session
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        # New session default
        return {
            "state": STATE_START,
            "data": {},
            "last_activity": time.time()
        }

    async def save_session(self, user_id, session):
        try:
            session["last_activity"] = time.time()
            await self.redis.set(f"session:{user_id}", json.dumps(session), ex=3600) # 1 hour expiry
        except Exception as e:
            logger.error(f"Redis save error: {e}")

    async def reset_session(self, user_id):
        session = {
            "state": STATE_START,
            "data": {},
            "last_activity": time.time()
        }
        await self.save_session(user_id, session)
            
    async def cleanup_loop(self):
        # Redis handles expiry automatically via 'ex' parameter
        pass

# Global instance
session_manager = SessionManager()
