import requests
import time
import threading
import uvicorn
from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

def test_new_flow():
    print("Starting New Flow Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8002/api/chat"
    user_id = "flow_tester_new"
    
    def send(msg):
        print(f"User: {msg}")
        res = requests.post(url, json={"user_id": user_id, "message": msg, "channel": "test"}).json()
        print(f"Bot: {res['reply']}")
        if res.get("ui_data"):
             print(f"UI Type: {res['ui_data'].get('type')}")
        return res

    # Step 1: Greeting
    send("Hallo")
    
    # Step 2: Tariffs (Should trigger Duration Selection)
    res = send("Zeig mir Tarife")
    assert res['ui_data']['type'] == "duration_selection"
    
    # Step 3: Select Duration (12 Months)
    res = send("12 Monate")
    assert res['ui_data']['type'] == "tariff_type_selection"
    
    # Step 4: Select Tariff Type (Single)
    res = send("Einzel")
    assert res['ui_data']['type'] == "product_selection"
    
    # Step 5: Select Product (First one)
    products = res['ui_data']['products']
    if products:
        first_product = products[0]['name']
        res = send(first_product)
        # Should ask for consumption
        assert res['ui_data']['type'] == "consumption_input"
    
    # Step 6: Consumption
    res = send("3500")
    assert res['ui_data']['type'] == "simulation_result"

    print("New Flow Test Completed Successfully.")

if __name__ == "__main__":
    test_new_flow()
