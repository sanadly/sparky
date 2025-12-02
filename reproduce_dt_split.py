import asyncio
import logging
from backend.services.chat_service import ChatService
from backend.session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    chat_service = ChatService()
    user_id = "test_dt_split@example.com"
    
    # Reset session
    session_manager.reset_session(user_id)
    
    # Pre-load products into session to simulate state
    # We need a DT product. Based on logs: INTENSIVE Day & Night Demo-Produkt (ID: INT_DNN_DEMO_PROD)
    session = session_manager.get_session(user_id)
    session["data"]["products"] = [
        {"produktId": "INT_DNN_DEMO_PROD", "name": "INTENSIVE Day & Night Demo-Produkt", "bezeichnung": "INTENSIVE Day & Night Demo-Produkt", "etDt": "DT"}
    ]
    session["state"] = "WAITING_FOR_CONSUMPTION"
    
    print("\n--- Test Case: 'INTENSIVE Day & Night, wir sind 2 Personen' ---")
    response = await chat_service.handle_message(user_id, "Ich nehme den INTENSIVE Day & Night Demo-Produkt, wir sind 2 Personen")
    print(f"User: Ich nehme den INTENSIVE Day & Night Demo-Produkt, wir sind 2 Personen")
    print(f"Bot: {response.get('reply')}")
    
    # Check if it simulated (Success) or asked for split (Fail)
    reply = response.get('reply', '')
    if "Preis" in reply or "Euro" in reply or "€" in reply or "auf Anfrage" in reply:
        print("✅ Result: SUCCESS (Simulated price)")
    elif "HT" in reply and "NT" in reply:
        print("❌ Result: FAILURE (Asked for HT/NT split)")
    else:
        print(f"❓ Result: UNKNOWN (Reply: {reply})")

if __name__ == "__main__":
    asyncio.run(reproduce())
