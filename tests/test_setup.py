import sys
import os

# Add parent directory to path to allow importing backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.sap_client import sap_client
from backend.services.llm_service import llm_service
import requests
import threading
import time
import uvicorn
from backend.main import app

def test_sap_client():
    print("Testing SAP Client...")
    token = sap_client.get_token()
    print(f"Token: {token}")
    
    products = sap_client.get_products(token)
    print(f"Products: {products}")
    
    sim = sap_client.simulate_price(token, 1000, "PROD-1")
    print(f"Simulation: {sim}")
    
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    offer = sap_client.create_offer(token, "PROD-1", future_date, {"name": "Test User"})
    print(f"Offer: {offer}")
    print("-" * 20)

def test_llm_service():
    print("Testing LLM Service...")
    answer = llm_service.generate_answer("Hello")
    print(f"LLM Answer: {answer}")
    print("-" * 20)

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

def test_backend_integration():
    print("Testing Backend Integration...")
    # Start server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2) # Wait for server to start
    
    url = "http://127.0.0.1:8001/api/chat"
    
    # Test 1: Greeting
    payload = {"user_id": "test_user", "message": "Hallo", "channel": "test"}
    res = requests.post(url, json=payload).json()
    print(f"Greeting Response: {res}")
    
    # Test 2: Tariff
    payload = {"user_id": "test_user", "message": "Zeig mir Tarife", "channel": "test"}
    res = requests.post(url, json=payload).json()
    print(f"Tariff Response: {res}")
    
    # Test 3: LLM Fallback
    payload = {"user_id": "test_user", "message": "Was ist der Sinn des Lebens?", "channel": "test"}
    res = requests.post(url, json=payload).json()
    print(f"LLM Response: {res}")
    print("-" * 20)

if __name__ == "__main__":
    test_sap_client()
    test_llm_service()
    test_backend_integration()
