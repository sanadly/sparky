import logging
import difflib
import re

# Mock logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Product Data
products = [
    {"produktId": "INT12", "bezeichnung": "INTENSIVE 12 Demo-Produkt"},
    {"produktId": "INT24", "bezeichnung": "INTENSIVE 24 Demo-Produkt"},
    {"produktId": "INT_DNN", "bezeichnung": "INTENSIVE Day & Night Demo-Produkt"},
    {"produktId": "INT_DNN24", "bezeichnung": "INTENSIVE Day & Night Demo-Produkt 24"},
]

def _find_product_in_text(text, products):
    """
    Helper to find a product in text using robust matching (Token Overlap + Fuzzy).
    Returns (product_id, product_name) or (None, None).
    """
    if not text or not products:
        return None, None

    def tokenize(s):
        return set(re.findall(r'\w+', s.lower()))

    user_tokens = tokenize(text)
    best_match = None
    best_score = 0.0

    for p in products:
        p_name = p.get('bezeichnung') or p.get('name', '')
        p_tokens = tokenize(p_name)
        
        if not p_tokens:
            continue

        # 1. Token Overlap Score (How much of the product is in the input?)
        common_tokens = user_tokens.intersection(p_tokens)
        product_overlap = len(common_tokens) / len(p_tokens)
        
        # 2. User Coverage Score (How much of the input is in the product?)
        user_coverage = len(common_tokens) / len(user_tokens) if user_tokens else 0.0
        
        # 3. Combined Score
        base_score = (product_overlap + user_coverage) / 2
        
        # 4. Phrase Bonus
        phrase_bonus = 0.2 if p_name.lower() in text.lower() else 0.0
        
        final_score = base_score + phrase_bonus
        
        print(f"Checking '{p_name}' against '{text}': Score={final_score:.2f} (P_Overlap={product_overlap:.2f}, U_Coverage={user_coverage:.2f})")

        if final_score > best_score:
            best_score = final_score
            best_match = p
        elif final_score == best_score and best_match:
             pass

    if best_match and best_score >= 0.5:
            p_name = best_match.get('bezeichnung') or best_match.get('name')
            return best_match.get("produktId"), p_name
            
    return None, None

# Test Cases
test_cases = [
    ("Ich wähle INTENSIVE 12", "INT12"),
    ("INTENSIVE 12 Demo-Produkt bitte", "INT12"),
    ("Ich möchte den INTENSIVE Day & Night", "INT_DNN"),
    ("INTENSIVE Day & Night 24", "INT_DNN24"),
    ("INTENSIVE", "INT12"), # Should pick one, likely INT12 or INT24, but let's see which one wins on length/tokens. 
    # Actually INTENSIVE is a substring of all. 
    # INTENSIVE 12 has tokens {intensive, 12, demo, produkt}. User has {intensive}. Overlap 1/4 = 0.25.
    # INTENSIVE Day & Night has {intensive, day, night, demo, produkt}. Overlap 1/5 = 0.2.
    # So INTENSIVE 12 should win over Day & Night.
    
    ("INTENSIVE 24", "INT24"),
    ("Day & Night", "INT_DNN"), # {day, night} vs {intensive, day, night, demo, produkt} -> 2/5 = 0.4. Might fail threshold 0.5.
    # Let's check if threshold 0.5 is too high for "Day & Night".
]

print("----------------------------------------------------------------")
print("RUNNING TESTS")
print("----------------------------------------------------------------")

for text, expected_id in test_cases:
    print(f"\nInput: '{text}'")
    pid, pname = _find_product_in_text(text, products)
    status = "✅ PASS" if pid == expected_id else f"❌ FAIL (Expected {expected_id}, got {pid})"
    print(f"Result: {pid} ({pname}) -> {status}")
