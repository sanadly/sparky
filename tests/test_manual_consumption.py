import requests
import time
import threading
import uvicorn
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="error")

def test_manual_consumption():
    print("Starting Manual Consumption Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8003/api/chat"
    user_id = "manual_tester"
    
    def send(msg):
        print(f"User: {msg}")
        headers = {"X-API-Key": "secret-api-key"}
        res = requests.post(url, json={"user_id": user_id, "message": msg, "channel": "test"}, headers=headers).json()
        print(f"Bot: {res['reply']}")
        return res

    # Step 1: Greeting / Reset
    send("Start")
    send("Hallo")
    
    # Step 2: Tariffs
    send("Zeig mir Tarife")
    
    # Step 2b: Duration
    send("12 Monate")
    
    # Step 2c: Tariff Type
    send("Einzeltarif")
    
    # Step 3: Product Choice (Select first product)
    send("INTENSIVE 12")
    
    # Step 4: Select Manual Consumption (simulated callback)
    res = send("manual")
    assert "bitte gib deinen jahresverbrauch" in res['reply'].lower()
    
    # Step 4: Send Value
    res = send("4200")
    # Check if simulation result is returned (price calculation)
    assert "kostet dich" in res['reply'].lower() or "angebot" in res['reply'].lower()
    
    print("Manual Consumption Test Completed Successfully.")

if __name__ == "__main__":
    test_manual_consumption()
