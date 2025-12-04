import requests
import time
import threading
import uvicorn
import sys
import os

# Add parent directory to path to allow importing backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

def test_flow():
    print("Starting Flow Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8002/api/chat"
    user_id = "flow_tester"
    
    def send(msg):
        print(f"User: {msg}")
        headers = {"X-API-Key": "secret-api-key"}
        res = requests.post(url, json={"user_id": user_id, "message": msg, "channel": "test"}, headers=headers).json()
        print(f"Bot: {res['reply']}")
        return res['reply']

    # Step 1: Greeting
    send("Hallo")
    
    # Step 2: Tariffs
    send("Zeig mir Tarife")
    
    # Step 3: Consumption
    send("Ich verbrauche 3500 kWh")
    
    # Step 4: Product Choice
    send("Green Energy")
    
    # Step 5: Offer Request
    send("Ja, bitte ein Angebot")
    
    # Step 6: Date
    send("Ab 01.01.2026")
    
    print("Flow Test Completed.")

if __name__ == "__main__":
    test_flow()
