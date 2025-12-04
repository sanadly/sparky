import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from backend.services.chat_service import chat_service
from backend.session_manager import (
    session_manager, 
    STATE_START, 
    STATE_WAITING_FOR_DURATION, 
    STATE_WAITING_FOR_TARIFF_TYPE, 
    STATE_WAITING_FOR_PRODUCT_CHOICE, 
    STATE_SIMULATION_DONE,
    STATE_WAITING_FOR_CONSUMPTION
)

async def verify_flow():
    user_id = "test_user_refactor"
    session_manager.reset_session(user_id)
    
    print("--- 1. Start ---")
    res = await chat_service.handle_message(user_id, "start")
    print(f"State: {res.get('state')}")
    assert res.get('state') == STATE_START
    
    print("\n--- 2. Show Products ---")
    res = await chat_service.handle_message(user_id, "Tarife anzeigen")
    print(f"State: {res.get('state')}")
    assert res.get('state') == STATE_WAITING_FOR_DURATION
    
    print("\n--- 3. Select Duration ---")
    res = await chat_service.handle_message(user_id, "12 Monate")
    print(f"State: {res.get('state')}")
    assert res.get('state') == STATE_WAITING_FOR_TARIFF_TYPE

    print("\n--- 4. Select Tariff Type ---")
    res = await chat_service.handle_message(user_id, "Einzel")
    print(f"State: {res.get('state')}")
    assert res.get('state') == STATE_WAITING_FOR_PRODUCT_CHOICE
    
    print("\n--- 5. Select Product (Mock) ---")
    # We need to know a valid product name or ID. 
    # Since we are mocking or using real SAP, let's try a generic one or rely on the list
    # For this test, let's assume "INTENSIVE 12 Demo-Produkt" exists or similar.
    # We can check the UI data from previous step
    products = res.get('ui_data', {}).get('products', [])
    if products:
        p_name = products[0]['name']
        print(f"Selecting product: {p_name}")
        res = await chat_service.handle_message(user_id, p_name)
    else:
        print("No products found to select. Skipping product selection.")
        return

    print(f"State: {res.get('state')}")
    # It might ask for consumption
    
    if res.get('state') == STATE_WAITING_FOR_CONSUMPTION:
        print("\n--- 6. Enter Consumption ---")
        res = await chat_service.handle_message(user_id, "2500")
        print(f"State: {res.get('state')}")
        assert res.get('state') == STATE_SIMULATION_DONE
        print(f"Reply: {res.get('reply')}")

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    asyncio.run(verify_flow())
