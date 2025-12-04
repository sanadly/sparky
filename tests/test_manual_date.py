import requests
import time
import threading
import uvicorn
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8004, log_level="error")

def test_manual_date():
    print("Starting Manual Date Test...")
    
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8004/api/chat"
    user_id = "date_tester"
    
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
    send("2500")
    
    # Step 5: Offer Request
    res = send("Ja, Angebot")
    assert "ab wann" in res['reply'].lower()
    
    # Step 6: Manual Date
    res = send("manual")
    assert "gewünschtes startdatum" in res['reply'].lower()
    
    # Step 7: Send Date
    future_date = (datetime.now() + timedelta(days=400)).strftime("%d.%m.%Y")
    res = send(future_date)
    assert "geschafft" in res['reply'].lower() or "angebot" in res['reply'].lower()
    
    print("Manual Date Test Completed Successfully.")

if __name__ == "__main__":
    test_manual_date()
