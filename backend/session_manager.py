import time
import logging
import asyncio

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
        self.sessions = {}

    def get_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "state": STATE_START,
                "data": {},
                "last_activity": time.time()
            }
        self.sessions[user_id]["last_activity"] = time.time()
        return self.sessions[user_id]

    def reset_session(self, user_id):
        if user_id in self.sessions:
            self.sessions[user_id]["state"] = STATE_START
            self.sessions[user_id]["data"] = {}
            
    async def cleanup_loop(self):
        while True:
            await asyncio.sleep(600) # Check every 10 mins
            now = time.time()
            to_delete = [uid for uid, s in self.sessions.items() if now - s["last_activity"] > 1800]
            for uid in to_delete:
                del self.sessions[uid]
                logger.info(f"Cleaned up session for {uid}")

# Global instance
session_manager = SessionManager()
