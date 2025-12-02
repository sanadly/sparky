import asyncio
import logging
from backend.services.chat_service import ChatService
from backend.session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    chat_service = ChatService()
    user_id = "test_user@example.com"
    
    # Reset session
    session_manager.reset_session(user_id)
    
    print("\n--- Test Case 1: 'Angebot' ---")
    response = await chat_service.handle_message(user_id, "Angebot")
    print(f"User: Angebot")
    print(f"Bot: {response.get('reply')}")
    print(f"State: {session_manager.get_session(user_id)['state']}")
    
    # Check if it asked for consumption or showed products (Success) or gave a generic answer (Fail)
    reply = response.get('reply', '')
    if any(x in reply for x in ["Verbrauch", "Tarife", "Laufzeit", "Monate"]):
        print("✅ Result: SUCCESS (Recognized intent)")
    else:
        print("❌ Result: FAILURE (Generic response)")

    print("\n--- Test Case 2: 'Re: Angebot' (Simulating reply) ---")
    # Simulate user replying to the generic email
    response = await chat_service.handle_message(user_id, "Re: Angebot")
    print(f"User: Re: Angebot")
    print(f"Bot: {response.get('reply')}")
    print(f"State: {session_manager.get_session(user_id)['state']}")

if __name__ == "__main__":
    asyncio.run(reproduce())
