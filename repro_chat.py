import asyncio
from backend.services.chat_service import chat_service
from backend.session_manager import session_manager

async def test_chat():
    user_id = "test_user_repro"
    
    print("--- Sending 'start' ---")
    response = await chat_service.handle_message(user_id, "start")
    print(f"Response: {response['reply']}")
    
    print("\n--- Sending 'Möchtest du den aktuellen Chat wirklich beenden und neu starten?' ---")
    response = await chat_service.handle_message(user_id, "Möchtest du den aktuellen Chat wirklich beenden und neu starten?")
    print(f"Response: {response['reply']}")

if __name__ == "__main__":
    asyncio.run(test_chat())
