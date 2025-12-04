import asyncio
import logging
from backend.services.chat_service import chat_service, email_service
from backend.logger import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

async def run_worker():
    logger.info("🚀 Starting Email Worker...")
    try:
        await email_service.run_email_polling(chat_service)
    except Exception as e:
        logger.error(f"❌ Email Worker failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("🛑 Email Worker stopped.")
