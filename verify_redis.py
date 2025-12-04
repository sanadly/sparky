import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from backend.session_manager import session_manager
from backend.services.chat_service import chat_service

async def verify_redis():
    user_id = "test_redis_user"
    
    print("--- 1. Reset Session ---")
    await session_manager.reset_session(user_id)
    
    print("--- 2. Get Session (should be START) ---")
    session = await session_manager.get_session(user_id)
    print(f"State: {session['state']}")
    assert session['state'] == "START"
    
    print("--- 3. Update Session via ChatService ---")
    # Simulate a message that changes state
    # "Tarife anzeigen" -> WAITING_FOR_DURATION
    res = await chat_service.handle_message(user_id, "Tarife anzeigen")
    print(f"Response State: {res.get('state')}")
    
    print("--- 4. Verify Persistence ---")
    # Fetch session again directly from manager (which fetches from Redis)
    session_new = await session_manager.get_session(user_id)
    print(f"Persisted State: {session_new['state']}")
    
    if session_new['state'] != res.get('state'):
        print(f"❌ Mismatch! Expected {res.get('state')}, got {session_new['state']}")
        print("Did ChatService call save_session?")
    else:
        print("\n✅ Redis Verification Successful!")

if __name__ == "__main__":
    asyncio.run(verify_redis())
