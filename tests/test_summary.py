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
    uvicorn.run(app, host="127.0.0.1", port=8006, log_level="error")

def test_summary():
    print("Starting Summary Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8006/api/chat"
    user_id = "summary_tester"
    
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
    send("Einzeltarif")
    
    # Step 3: Product
    send("INTENSIVE 12")
    
    # Step 4: Consumption
    res = send("2500")
    
    # Check for summary
    assert "Deine Auswahl" in res['reply']
    assert "INTENSIVE 12" in res['reply']
    assert "2500" in res['reply']
    
    print("Summary Test Completed Successfully.")

if __name__ == "__main__":
    test_summary()
