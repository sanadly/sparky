import asyncio
import logging
from backend.services.chat_service import ChatService
from backend.session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    chat_service = ChatService()
    user_id = "test_combined@example.com"
    
    # Reset session
    session_manager.reset_session(user_id)
    
    # Pre-load products into session to simulate state
    session = session_manager.get_session(user_id)
    session["data"]["products"] = [
        {"produktId": "INT12", "name": "INTENSIVE 12", "bezeichnung": "INTENSIVE 12"}
    ]
    session["state"] = "WAITING_FOR_CONSUMPTION" # Simulate being in consumption state
    
    print("\n--- Test Case: 'INTENSIVE 12, wir sind 2 Personen' ---")
    response = await chat_service.handle_message(user_id, "Ich nehme den INTENSIVE 12, wir sind 2 Personen")
    print(f"User: Ich nehme den INTENSIVE 12, wir sind 2 Personen")
    
    # Debug: Check extraction directly
    from backend.services.llm_service import llm_service
    entities = llm_service.extract_entities("Ich nehme den INTENSIVE 12, wir sind 2 Personen")
    print(f"DEBUG Entities: {entities}")

    print(f"Bot: {response.get('reply')}")
    
    # Check if it simulated (Success) or asked for consumption (Fail)
    reply = response.get('reply', '')
    if "Preis" in reply or "Euro" in reply or "€" in reply or "auf Anfrage" in reply:
        print("✅ Result: SUCCESS (Simulated price)")
    elif "Verbrauch" in reply or "kWh" in reply:
        print("❌ Result: FAILURE (Asked for consumption again)")
    else:
        print(f"❓ Result: UNKNOWN (Reply: {reply})")

if __name__ == "__main__":
    asyncio.run(reproduce())
