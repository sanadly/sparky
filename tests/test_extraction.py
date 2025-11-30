import llm_service
import os
from dotenv import load_dotenv

load_dotenv()

def test_extraction():
    print("Testing LLM Entity Extraction...")
    
    test_cases = [
        "Ich verbrauche 3500 kWh",
        "Mein Verbrauch liegt bei 4200",
        "Ich möchte den Green Energy Tarif",
        "Startdatum ist der 01.01.2026",
        "Ich nehme INTENSIVE 12 ab dem 2025-05-01",
        "Was kostet der Spaß?" # Should return empty or partial
    ]
    
    for text in test_cases:
        print(f"\nInput: '{text}'")
        entities = llm_service.extract_entities(text)
        print(f"Extracted: {entities}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not found. Test will use Regex fallback (which is NOT what we want to test).")
    else:
        test_extraction()
