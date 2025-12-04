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
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="error")

def test_dt_input():
    print("Starting DT Input Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8005/api/chat"
    user_id = "dt_tester"
    
    def send(msg):
        print(f"User: {msg}")
        headers = {"X-API-Key": "secret-api-key"}
        res = requests.post(url, json={"user_id": user_id, "message": msg, "channel": "test"}, headers=headers).json()
        print(f"Bot: {res['reply']}")
        return res

    # Step 1: Reset
    send("Start")
    send("Hallo")
    
    # Step 2: Tariffs
    send("Zeig mir Tarife")
    send("12 Monate")
    send("Doppeltarif")
    
    # Step 3: Product (Select a DT product)
    # Assuming "INTENSIVE Day & Night Demo-Produkt" is available
    send("INTENSIVE Day & Night Demo-Produkt")
    
    # Step 4: Consumption (Single Value)
    # This should now trigger the default split and proceed to simulation
    res = send("3000")
    
    # Check if simulation succeeded (price calculation)
    assert "kostet dich" in res['reply'].lower() or "angebot" in res['reply'].lower()
    
    print("DT Input Test Completed Successfully.")

if __name__ == "__main__":
    test_dt_input()
