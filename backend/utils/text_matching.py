import re
import logging

logger = logging.getLogger(__name__)

def find_product_in_text(text, products):
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
        # This helps when user types a short, specific part of the name (e.g. "Day & Night")
        user_coverage = len(common_tokens) / len(user_tokens) if user_tokens else 0.0
        
        # 3. Combined Score
        # We weight them equally.
        base_score = (product_overlap + user_coverage) / 2
        
        # 4. Phrase Bonus (Boost if exact phrase appears)
        phrase_bonus = 0.2 if p_name.lower() in text.lower() else 0.0
        
        final_score = base_score + phrase_bonus
        
        if final_score > best_score:
            best_score = final_score
            best_match = p
        elif final_score == best_score and best_match:
            # Tie-breaker: Prefer longer product name (more specific) if scores are equal?
            pass

    # Threshold: At least 50% of product tokens must match, or exact phrase match
    if best_match and best_score >= 0.5:
            p_name = best_match.get('bezeichnung') or best_match.get('name')
            logger.info(f"🎯 Robust match: {p_name} (Score: {best_score:.2f})")
            return best_match.get("produktId"), p_name
            
    return None, None
