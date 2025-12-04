import logging
import re
from ..services.sap_client import SAPClient

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self, sap_client: SAPClient):
        self.sap_client = sap_client

    async def get_products(self):
        token = await self.sap_client.get_token()
        return await self.sap_client.get_products(token)

    def find_product_in_text(self, text, products):
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

            # 1. Token Overlap Score
            common_tokens = user_tokens.intersection(p_tokens)
            product_overlap = len(common_tokens) / len(p_tokens)
            
            # 2. User Coverage Score
            user_coverage = len(common_tokens) / len(user_tokens) if user_tokens else 0.0
            
            # 3. Combined Score
            base_score = (product_overlap + user_coverage) / 2
            
            # 4. Phrase Bonus
            phrase_bonus = 0.2 if p_name.lower() in text.lower() else 0.0
            
            final_score = base_score + phrase_bonus
            
            if final_score > best_score:
                best_score = final_score
                best_match = p
            elif final_score == best_score and best_match:
                pass

        # Threshold: At least 50% of product tokens must match, or exact phrase match
        if best_match and best_score >= 0.5:
             p_name = best_match.get('bezeichnung') or best_match.get('name')
             logger.info(f"🎯 Robust match: {p_name} (Score: {best_score:.2f})")
             return best_match.get("produktId"), p_name
             
        return None, None

    async def get_product_ui_data(self, products, consumption=None, simulation_service=None):
        products_data = []
        
        # Use provided consumption or default to 2500
        sim_consumption = 2500
        if consumption:
            try:
                sim_consumption = float(consumption)
            except ValueError:
                pass
        
        logger.info(f"🎯 PROCESSING {len(products)} PRODUCTS FOR UI (Consumption: {sim_consumption})")
        
        for p in products:
             # Simulate price
             product_id = p.get("produktId")
             base_price = 0.0
             working_price = 0.0
             total_price = 0.0
             
             logger.info(f"🔍 Processing product: {p.get('bezeichnung')} (ID: {product_id})")
             
             if product_id and simulation_service:
                 # Determine consumption split
                 sim_result, _, _ = await simulation_service.simulate_price(product_id, sim_consumption, product=p)
                 
                 if sim_result:
                     logger.info(f"✅ Simulation result keys: {sim_result.keys()}")
                     # Extract total from BillSimulation wrapper
                     sim_data = sim_result.get("BillSimulation", {})
                     total_price = float(sim_data.get("NET_AMOUNT", 0.0))
                     
                     # Extract components from product data directly
                     base_price = float(p.get("grundpreis", 0.0))
                     # Working price is in EUR/kWh, convert to Cents/kWh
                     working_price = float(p.get("preisET_HT", 0.0)) * 100
                     
                     logger.info(f"💵 Extracted prices - Base: {base_price}, Working: {working_price}, Total: {total_price}")
                 else:
                     logger.warning(f"⚠️ No simulation result for product {product_id}")
                     # Fallback to product data if simulation fails
                     base_price = float(p.get("grundpreis", 0.0))
                     working_price = float(p.get("preisET_HT", 0.0)) * 100
             else:
                 # Fallback if no simulation service or ID
                 base_price = float(p.get("grundpreis", 0.0))
                 working_price = float(p.get("preisET_HT", 0.0)) * 100

             products_data.append({
                 "id": p.get("produktId"),
                 "name": p.get("bezeichnung") or p.get("name"),
                 "description": p.get("beschreibung", ""),
                 "isGreen": any(x in (p.get("bezeichnung") or "").lower() for x in ["oeko", "öko", "green", "day & night", "day and night"]) or p.get("oeko", False),
                 "basePrice": base_price,
                 "workingPrice": working_price,
                 "totalPrice": total_price,
                 "contractDuration": p.get("laufzeit", 12)
             })
        
        logger.info(f"📤 SENDING TO FRONTEND: {products_data}")
        return {"type": "product_selection", "products": products_data} 
