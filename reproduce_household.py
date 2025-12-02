import asyncio
import logging
from backend.services.chat_service import ChatService
from backend.session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    chat_service = ChatService()
    user_id = "test_household@example.com"
    
    # Reset session
    session_manager.reset_session(user_id)
    
    print("\n--- Test Case: '2 Personen' ---")
    # Simulate user asking for recommendation for 2 people
    response = await chat_service.handle_message(user_id, "Wir sind 2 Personen, was empfiehlst du?")
    print(f"User: Wir sind 2 Personen, was empfiehlst du?")
    print(f"Bot: {response.get('reply')}")
    
    # Check if it estimated consumption (Success) or asked for number (Fail)
    reply = response.get('reply', '')
    if "2500" in reply or "3500" in reply: # Expected estimate for 2 people
        print("✅ Result: SUCCESS (Estimated consumption)")
    elif "Jahresverbrauch" in reply or "Zahl" in reply:
        print("❌ Result: FAILURE (Asked for explicit number)")
    else:
        print(f"❓ Result: UNKNOWN (Reply: {reply})")

if __name__ == "__main__":
    asyncio.run(reproduce())
