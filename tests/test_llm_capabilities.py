import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/chat"
USER_ID = "test_llm_user"

def send_message(message):
    try:
        response = requests.post(
            BASE_URL, 
            json={"user_id": USER_ID, "message": message, "channel": "test"}
        )
        response.raise_for_status()
        return response.json().get("reply", "")
    except Exception as e:
        print(f"Error: {e}")
        return ""

def test_llm_capabilities():
    print("Running LLM Capability Test...")
    print("-" * 30)

    # Test Cases
    test_inputs = [
        "Wer bist du?",
        "Was kannst du?",
        "Erzähl mir einen Witz",
        "Was ist der Sinn des Lebens?" # Should trigger fallback
    ]

    for msg in test_inputs:
        print(f"User: {msg}")
        reply = send_message(msg)
        print(f"Bot:  {reply}")
        print("-" * 30)
        
        # Simple assertions
        if not reply:
            print("❌ No reply received!")
            sys.exit(1)
            
    print("✅ LLM Capability Test Completed.")

if __name__ == "__main__":
    test_llm_capabilities()
