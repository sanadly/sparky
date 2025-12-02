import logging
import re
from datetime import datetime
from ..config import settings
from ..services.sap_client import SAPClient
from ..services.llm_service import LLMService

from ..session_manager import (
    session_manager,
    STATE_START,
    STATE_WAITING_FOR_CONSUMPTION,
    STATE_WAITING_FOR_PRODUCT_CHOICE,
    STATE_SIMULATION_DONE,
    STATE_WAITING_FOR_DATE,
    STATE_OFFER_CREATED,
    STATE_WAITING_FOR_DURATION,
    STATE_WAITING_FOR_TARIFF_TYPE
)

logger = logging.getLogger(__name__)

# Instantiate services globally as they were before
sap_client = SAPClient()
llm_service = LLMService()
# session_manager is imported

class ChatService:
    def _find_product_in_text(self, text, products):
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
                # Actually, for "INTENSIVE" input:
                # INT12: (0.25 + 1.0)/2 = 0.625
                # INT_DNN: (0.2 + 1.0)/2 = 0.6
                # So INT12 wins naturally because it's shorter (higher product_overlap).
                # But if user types "INTENSIVE 12", we want INT12.
                # INT12: (0.5 + 1.0)/2 = 0.75
                # INT_DNN: (0.2 + 0.5)/2 = 0.35
                # So INT12 wins.
                pass

        # Threshold: At least 50% of product tokens must match, or exact phrase match
        if best_match and best_score >= 0.5:
             p_name = best_match.get('bezeichnung') or best_match.get('name')
             logger.info(f"🎯 Robust match: {p_name} (Score: {best_score:.2f})")
             return best_match.get("produktId"), p_name
             
        return None, None

    async def handle_message(self, user_id, text):
        session = session_manager.get_session(user_id)
        state = session["state"]
        data = session["data"]
        text_lower = text.lower()
        
        response_text = ""
        
        # Global Intents
        if "reset" in text_lower or "start" in text_lower:
            session_manager.reset_session(user_id)
            return {
                 "reply": "**Hallo!** 👋 Ich bin **Sparky**, dein Energieberater der INTENSE AG.\n\nMöchtest du unsere Tarife sehen, eine Simulation starten oder hast du eine Frage?",
                 "state": STATE_START,
                 "quick_replies": ["Tarife anzeigen", "Simulation starten", "Was kannst du?"]
             }

        # Direct Product Selection (Bypass LLM)
        if text.startswith("SELECT_PRODUCT:"):
            product_id = text.split(":", 1)[1]
            session["data"]["product_id"] = product_id
            # Find product name for the reply
            products = session["data"].get("products", [])
            # If products not in session (e.g. restart), try to fetch or just use ID
            if not products:
                 token = sap_client.get_token()
                 products = sap_client.get_products(token)
                 session["data"]["products"] = products
            
            product_name = next((p.get('bezeichnung') or p.get('name') for p in products if p.get('produktId') == product_id), "Gewählter Tarif")
            session["data"]["product_name"] = product_name
            
            # Check if we have consumption
            if not session["data"].get("consumption") and not session["data"].get("consumption_r1"):
                 # Ask for consumption
                 full_product = next((p for p in products if p.get('produktId') == product_id), None)
                 is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
                 
                 logger.info(f"DEBUG: SELECT_PRODUCT id={product_id}, is_dt={is_dt}, full_product found={full_product is not None}")
                 
                 msg = f"Gute Wahl! Der {product_name} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh."
                 if is_dt:
                     msg = f"Gute Wahl! Der {product_name} ist ein Doppeltarif. Bitte nenne mir deinen Verbrauch für Tag (HT) und Nacht (NT) separat (z.B. 2000 HT und 1000 NT)."
                 
                 session["state"] = STATE_WAITING_FOR_CONSUMPTION
                 return {
                     "reply": msg,
                     "state": STATE_WAITING_FOR_CONSUMPTION,
                     "ui_data": {"type": "consumption_input", "is_dt": is_dt}
                 }

            return await self._run_simulation(session)

        # State Machine
        if state == STATE_START:
            return await self._handle_start(session, text_lower, text)
        elif state == STATE_WAITING_FOR_CONSUMPTION:
            return await self._handle_consumption(session, text)
        elif state == STATE_WAITING_FOR_PRODUCT_CHOICE:
            return await self._handle_product_choice(session, text)
        elif state == STATE_SIMULATION_DONE:
            return await self._handle_simulation_done(session, text, user_id)
        elif state == STATE_WAITING_FOR_DATE:
            return await self._handle_date(session, text, user_id)
        elif state == STATE_OFFER_CREATED:
            return await self._handle_offer_created(session, text)
        elif state == STATE_WAITING_FOR_DURATION:
            return await self._handle_duration(session, text)
        elif state == STATE_WAITING_FOR_TARIFF_TYPE:
            return await self._handle_tariff_type(session, text)
        
        # Fallback
        return {"reply": llm_service.generate_answer(text)}

    async def _handle_start(self, session, text_lower, text):
        # 1. Explicit request for products OR Affirmation (User says "Ja" to "Möchtest du Tarife sehen?")
        if any(x in text_lower for x in ["tarif", "produkte", "angebot", "zeig", "ja", "gerne", "ok", "sicher", "klar", "mach"]):
            token = sap_client.get_token()
            products = sap_client.get_products(token)
            if not products:
                return {"reply": "Entschuldigung, mein Tarifrechner macht gerade Pause. Bitte versuche es später."}
            
            product_lines = [f"- {p.get('bezeichnung') or p.get('name', 'Unbekannt')}" for p in products]
            product_list = "\n".join(product_lines)
            
            session["state"] = STATE_WAITING_FOR_DURATION
            session["data"]["products"] = products
            
            return {
                "reply": "Gerne! Für welche Laufzeit interessierst du dich? (12 Monate, 24 Monate oder egal)",
                "state": STATE_WAITING_FOR_DURATION,
                "ui_data": {"type": "duration_selection"} 
            }

        # 2. Simple Greeting
        elif any(x in text_lower for x in ["hallo", "hi", "hey", "start"]):
             return {
                 "reply": "**Hallo!** 👋 Ich bin **Sparky**, dein Energieberater der INTENSE AG.\n\nMöchtest du unsere Tarife sehen, eine Simulation starten oder hast du eine Frage?",
                 "state": STATE_START,
                 "quick_replies": ["Tarife anzeigen", "Simulation starten", "Was kannst du?"]
             }
            
        # 3. Simulation Request
        elif any(x in text_lower for x in ["simulat", "berechnen", "rechnen", "kosten"]):
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return {
                 "reply": "Gerne! Für eine genaue Simulation benötige ich deinen Jahresverbrauch.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }
        # 4. Check for Consumption (Implicit Simulation Start)
        entities = llm_service.extract_entities(text)
        if "consumption" in entities:
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             # Pass to _handle_consumption to process the data immediately
             return await self._handle_consumption(session, text)

        else:
            context = {"state": "start", "instruction": "Du bist ein Energieberater. Beantworte die Frage kurz und frage dann: 'Möchtest du unsere Tarife sehen?'"}
            return {"reply": llm_service.generate_answer(text, context)}

    async def _handle_consumption(self, session, text):
        # 0. Check for Direct Product Match first (User might have ignored consumption question and selected product)
        products = session["data"].get("products", [])
        p_id, p_name = self._find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            logger.info(f"🎯 Direct text match found in _handle_consumption: {p_name}")
            
            # If we also have consumption in the text (e.g. "I want Product X and use 2500 kWh"), extract it
            entities = llm_service.extract_entities(text)
            
            # Check if it is DT to ask correctly
            token = sap_client.get_token()
            products = session["data"].get("products", [])
            if not products:
                 products = sap_client.get_products(token)
            
            check_id = p_id or session["data"].get("product_id")
            full_product = next((p for p in products if p.get('produktId') == check_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if "consumption" in entities:
                if is_dt:
                     # User gave 1 value for DT product -> Ask for split
                     pass # Fall through to return reply below
                else:
                    session["data"]["consumption"] = entities["consumption"]
                    session["data"]["consumption_r1"] = entities["consumption"]
                    session["data"]["consumption_r2"] = ""
                    return await self._run_simulation(session)
            elif "consumption_r1" in entities and "consumption_r2" in entities:
                session["data"]["consumption"] = entities["consumption_r1"] + entities["consumption_r2"]
                session["data"]["consumption_r1"] = entities["consumption_r1"]
                session["data"]["consumption_r2"] = entities["consumption_r2"]
                return await self._run_simulation(session)
            
            # Otherwise, just switch product and ask for consumption again
            msg = f"Gute Wahl! Der {p_name} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh."
            if is_dt:
                msg = f"Gute Wahl! Der {p_name} ist ein Doppeltarif. Bitte nenne mir deinen Verbrauch für Tag (HT) und Nacht (NT) separat (z.B. 2000 HT und 1000 NT)."

            return {
                 "reply": msg,
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        entities = llm_service.extract_entities(text)
        logger.debug(f"Extracted entities in _handle_consumption: {entities}")
        
        if "consumption" in entities:
            # Check if it is DT to ask correctly
            token = sap_client.get_token()
            products = session["data"].get("products", [])
            if not products:
                 products = sap_client.get_products(token)
            
            check_id = session["data"].get("product_id")
            full_product = next((p for p in products if p.get('produktId') == check_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if is_dt:
                 # User gave 1 value for DT product -> Ask for split
                 msg = f"Für den Tarif {full_product.get('bezeichnung')} (Doppeltarif) benötige ich deinen Verbrauch für Tag (HT) und Nacht (NT) separat. Bitte nenne mir beide Werte."
                 return {
                     "reply": msg,
                     "state": STATE_WAITING_FOR_CONSUMPTION,
                     "ui_data": {"type": "consumption_input", "is_dt": True}
                 }

            session["data"]["consumption"] = entities["consumption"]
            session["data"]["consumption_r1"] = entities["consumption"]
            session["data"]["consumption_r2"] = ""
            
            # If we already have a product stored from a previous turn, go to simulation
            if "product_name" in session["data"]:
                 return await self._run_simulation(session)

            if "product_name" in entities:
                session["data"]["product_name"] = entities["product_name"]
                return await self._run_simulation(session)
            
            session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
            return {
                "reply": f"Verstanden, {entities['consumption']} kWh. Welchen der Tarife möchtest du wählen?",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE,
                "ui_data": self._get_product_ui_data(session["data"].get("products", []))
            }
        
        elif "consumption_r1" in entities and "consumption_r2" in entities:
            session["data"]["consumption_r1"] = entities["consumption_r1"]
            session["data"]["consumption_r2"] = entities["consumption_r2"]
            session["data"]["consumption"] = entities["consumption_r1"] + entities["consumption_r2"]
            
            if "product_name" in session["data"]:
                 return await self._run_simulation(session)
                 
            session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
            return {
                "reply": f"Verstanden, {entities['consumption_r1']} kWh (HT) und {entities['consumption_r2']} kWh (NT). Welchen der Tarife möchtest du wählen?",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE,
                "ui_data": self._get_product_ui_data(session["data"].get("products", []))
            }
        
        # User selected a product but didn't give consumption yet (LLM fallback)
        elif "product_name" in entities:
             session["data"]["product_name"] = entities["product_name"]
             return {
                 "reply": f"Gute Wahl! Der {entities['product_name']} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh.",
                 "state": STATE_WAITING_FOR_CONSUMPTION, # Stay in this state
                 "ui_data": {"type": "consumption_input"}
             }

        else:
            # Handle fallback logic (questions, offers without consumption, etc.)
            text_lower = text.lower()
            if "angebot" in text_lower:
                return {"reply": "Gerne erstelle ich dir ein Angebot! Dafür brauche ich zunächst deinen Jahresverbrauch in kWh."}
            elif any(word in text_lower for word in ["was", "wie", "warum", "welche", "?", "erkläre"]):
                 context = {"state": "waiting_for_consumption", "products": session["data"].get("products", [])}
                 return {"reply": llm_service.generate_answer(text, context)}
            
            return {"reply": "Das habe ich nicht verstanden. Bitte nenne mir deinen Jahresverbrauch als Zahl (z.B. 3500)."}

    async def _handle_product_choice(self, session, text):
        # 0. Direct Text Matching (Most Accurate for Manual Input)
        products = session["data"].get("products", [])
        p_id, p_name = self._find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            logger.info(f"🎯 Direct text match found: {p_name}")
            
            # Check if DT and if we need more consumption data
            token = sap_client.get_token()
            products = session["data"].get("products", [])
            full_product = next((p for p in products if p.get('produktId') == p_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if is_dt and not session["data"].get("consumption_r2"):
                return {
                    "reply": f"Für den Tarif {p_name} (Doppeltarif) benötige ich deinen Verbrauch für Tag (HT) und Nacht (NT) separat. Bitte nenne mir beide Werte.",
                    "state": STATE_WAITING_FOR_CONSUMPTION,
                    "ui_data": {"type": "consumption_input", "is_dt": True}
                }
                
            return await self._run_simulation(session)

        extraction = llm_service.extract_entities(text)
        intent = extraction.get("intent", "unknown")
        data = session["data"]
        
        if intent == "correction" and "consumption" in extraction:
            data["consumption"] = extraction["consumption"]
            return {
                "reply": f"Okay, ich korrigiere den Verbrauch auf {data['consumption']} kWh. Welchen Tarif möchtest du wählen?",
                "ui_data": self._get_product_ui_data(data.get("products", []))
            }
            
        elif "product_name" in extraction:
            data["product_name"] = extraction["product_name"]
            return await self._run_simulation(session)
            
        elif intent in ["recommendation", "question"]:
            context = {
                "state": "product_choice",
                "consumption": data.get("consumption"),
                "products": [p.get("bezeichnung") or p.get("name") for p in data.get("products", [])],
                "instruction": f"Der Kunde hat {data.get('consumption')} kWh Jahresverbrauch und fragt: '{text}'. Analysiere die verfügbaren Tarife und empfehle den passendsten."
            }
            reply = llm_service.generate_answer(text, context)
            # Try to infer product from LLM response
            for p in data.get("products", []):
                p_name = p.get("bezeichnung") or p.get("name", "")
                if p_name.upper() in reply.upper():
                    data["last_recommendation"] = p_name
                    break
            return {"reply": reply}

        elif intent == "confirmation" and "last_recommendation" in data:
            data["product_name"] = data["last_recommendation"]
            return await self._run_simulation(session)
            
        # Fallback: Check if text matches a product name loosely (already covered by step 0 but kept for safety)
        for p in data.get("products", []):
            p_name = p.get('bezeichnung') or p.get('name', '')
            if text.lower() in p_name.lower() or p_name.lower() in text.lower():
                data["product_name"] = p_name
                return await self._run_simulation(session)

        # Check for general "Show Tariffs" intent
        if any(x in text.lower() for x in ["tarif", "zeig", "liste", "angebot", "welche"]):
             return {
                "reply": "Hier sind unsere verfügbaren Tarife. Welchen möchtest du wählen?",
                "ui_data": self._get_product_ui_data(data.get("products", []))
            }

        return {"reply": "Das habe ich nicht verstanden. Welchen Tarif möchtest du wählen? (Oder frag mich nach einer Empfehlung!)"}

    async def _handle_simulation_done(self, session, text, user_id):
        text_lower = text.lower()
        if "änder" in text_lower and ("verbrauch" in text_lower or "kwh" in text_lower):
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return {"reply": "Kein Problem! Wie hoch ist dein neuer Jahresverbrauch in kWh?", "ui_data": {"type": "consumption_input"}}
        elif any(x in text_lower for x in ["angebot", "ja", "sicher", "nehm", "haben", "kauf", "ok", "gerne", "machen", "bestell"]):
            session["state"] = STATE_WAITING_FOR_DATE
            return {
                "reply": "Super! Das sichere ich dir gerne. ⚡ Ab wann soll der Vertrag laufen? (z.B. 01.01.2026)",
                "state": STATE_WAITING_FOR_DATE,
                "ui_data": {"type": "date_input"}
            }
        elif "nein" in text_lower:
            session_manager.reset_session(user_id)
            session["state"] = STATE_START
            session["data"] = {}
            return {"reply": "Alles klar. Kann ich sonst noch etwas für dich tun?"}
        
        # Check if user provided a date directly
        if llm_service.extract_entities(text).get("date"):
            session["state"] = STATE_WAITING_FOR_DATE
            return await self._handle_date(session, text, user_id)
            
        context = {"state": "simulation_done", "consumption": session["data"].get("consumption"), "product": session["data"].get("product_name")}
        return {"reply": llm_service.generate_answer(text, context)}

    async def _handle_date(self, session, text, user_id):
        entities = llm_service.extract_entities(text)
        if "date" in entities:
            start_date = entities["date"]
            # Validation logic (simplified for brevity, original logic was good but long)
            # Assuming date is valid for now or adding basic check
            # Validation logic
            date_obj = None
            try:
                # Try standard ISO format first (LLM output)
                date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            except ValueError:
                try:
                    # Try German format (User input / Fallback)
                    date_obj = datetime.strptime(start_date.strip(), "%d.%m.%Y")
                except ValueError:
                    return {"reply": "Ungültiges Datumsformat. Bitte nutze TT.MM.JJJJ."}
            
            if date_obj < datetime.now():
                 return {"reply": "Das Datum liegt in der Vergangenheit. Bitte nenne ein Datum in der Zukunft."}
            
            # Normalize to ISO for SAP and Session
            start_date_iso = date_obj.strftime("%Y-%m-%d")
            session["data"]["start_date"] = start_date_iso
            
            try:
                token = sap_client.get_token()
                product_id = session["data"].get("product_id", "INT12_DEMO_PROD")
                
                # Retrieve consumption and split if necessary
                consumption = session["data"].get("consumption", "2500")
                consumption_r1 = consumption
                consumption_r2 = ""
                
                products = session["data"].get("products", [])
                if not products:
                     products = sap_client.get_products(token)
                
                full_product = next((p for p in products if p.get('produktId') == product_id), None)
                
                consumption_r1, consumption_r2 = self._get_consumption_split(full_product, consumption)

                offer, error_msg = sap_client.create_offer(token, product_id, start_date_iso, consumption_r1, consumption_r2, {"user_id": user_id})
                if offer:
                    logger.info(f"✅ OFFER RESPONSE: {offer}")
                    # Extract ID logic
                    offer_data = offer
                    if "d" in offer:
                        offer_data = offer["d"]
                        if "results" in offer_data and isinstance(offer_data["results"], list) and offer_data["results"]:
                            offer_data = offer_data["results"][0]
                    elif "value" in offer:
                        if isinstance(offer["value"], list) and offer["value"]:
                            offer_data = offer["value"][0]
                        elif isinstance(offer["value"], dict):
                            offer_data = offer["value"]
                        
                    offer_id = offer_data.get("displayId") or offer_data.get("offer_id") or offer_data.get("ID") or offer_data.get("Angebotsnummer") or offer_data.get("ObjectID") or offer.get("offer_id")
                
                    # Capture data before reset
                    product_name = session["data"].get("product_name", "Stromtarif")
                    
                    # Reset session after successful offer
                    session_manager.reset_session(user_id) # Changed session_id to user_id
                    session["state"] = STATE_START
                    session["data"] = {}
                    
                    return {
                        "reply": f"Geschafft! 🎉 Hier ist dein Angebot: {offer_id}",
                        "state": STATE_OFFER_CREATED,
                        "ui_data": {
                            "type": "offer_success", 
                            "offer_id": offer_id,
                            "product_name": product_name
                        }
                    }
                else:
                    return {"reply": f"Fehler bei der Angebotserstellung: {error_msg or 'Bitte versuche es später.'}"}
            except Exception as e:
                logger.error(f"Error creating offer: {e}")
                return {"reply": "Es ist ein Fehler aufgetreten. Bitte versuche es später noch einmal."}
        
        return {"reply": "Ich konnte kein Datum erkennen. Bitte nenne ein Datum (z.B. 01.01.2026)."}

    async def _handle_offer_created(self, session, text):
        if any(w in text.lower() for w in ["danke", "tschüss"]):
            session["state"] = STATE_START
            session["data"] = {}
            return {"reply": "Gerne! Bis zum nächsten Mal."}
        
        if any(w in text.lower() for w in ["zeig", "angebot", "sehen", "wo"]):
             return {
                 "reply": "Hier ist dein Angebot noch einmal:",
                 "ui_data": {
                        "type": "offer_success", 
                        "offer_id": session["data"].get("last_offer_id", "Unknown"),
                        "product_name": session["data"].get("product_name", "Stromtarif")
                    }
             }

        context = {"state": "offer_created", "offer_id": session["data"].get("last_offer_id")}
        return {"reply": llm_service.generate_answer(text, context)}

    async def _handle_duration(self, session, text):
        text_lower = text.lower()
        duration = None
        
        if "12" in text_lower:
            duration = 12
        elif "24" in text_lower:
            duration = 24
        elif any(x in text_lower for x in ["egal", "alle", "beide"]):
            duration = "egal"
            
        if duration:
            session["data"]["filter_duration"] = duration
            session["state"] = STATE_WAITING_FOR_TARIFF_TYPE
            return {
                "reply": "Alles klar. Benötigst du einen Einzel- oder Doppeltarif? (Einzel, Doppel oder egal)",
                "state": STATE_WAITING_FOR_TARIFF_TYPE,
                "ui_data": {"type": "tariff_type_selection"}
            }
        
        return {"reply": "Das habe ich nicht verstanden. Bitte wähle 12, 24 oder egal."}

    async def _handle_tariff_type(self, session, text):
        text_lower = text.lower()
        tariff_type = None
        
        if any(x in text_lower for x in ["einzel", "single", "standard"]):
            tariff_type = "single"
        elif any(x in text_lower for x in ["doppel", "double", "ht/nt", "ht", "nt"]):
            tariff_type = "double"
        elif any(x in text_lower for x in ["egal", "alle", "beide"]):
            tariff_type = "egal"
            
        if tariff_type:
            session["data"]["filter_tariff_type"] = tariff_type
            
            # Filter products
            all_products = session["data"].get("products", [])
            filtered_products = []
            
            filter_duration = session["data"].get("filter_duration")
            
            for p in all_products:
                # Duration Filter
                if filter_duration != "egal":
                    if int(p.get("laufzeit", 12)) != int(filter_duration):
                        continue
                
                # Tariff Type Filter
                if tariff_type != "egal":
                    is_double = p.get('etDt') == 'DT' or p.get('preisNT') is not None
                    if tariff_type == "single" and is_double:
                        continue
                    if tariff_type == "double" and not is_double:
                        continue
                        
                filtered_products.append(p)
            
            if not filtered_products:
                 return {
                    "reply": "Leider habe ich keine passenden Tarife gefunden. Möchtest du alle Tarife sehen?",
                    "state": STATE_WAITING_FOR_DURATION, # Or back to start?
                    "ui_data": {"type": "duration_selection"} # Let them try again
                }

            session["state"] = STATE_WAITING_FOR_CONSUMPTION # Or product choice directly?
            # Let's show products and ask for consumption if they select one, or ask for consumption generally
            
            product_lines = [f"- {p.get('bezeichnung') or p.get('name', 'Unbekannt')}" for p in filtered_products]
            product_list = "\n".join(product_lines)
            
            return {
                "reply": f"Hier sind die passenden Tarife:\n\n{product_list}\n\nWelchen möchtest du wählen? (Oder nenne mir deinen Verbrauch für eine Berechnung)",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE, # Changed to choice to allow selection
                "ui_data": {"type": "product_selection", "products": self._get_product_ui_data(filtered_products)["products"]}
            }
            
        return {"reply": "Das habe ich nicht verstanden. Bitte wähle Einzel, Doppel oder egal."}

    def _get_consumption_split(self, product, total_consumption):
        """
        Helper to split consumption for Double Tariff products.
        Returns (consumption_r1, consumption_r2)
        """
        consumption_r1 = total_consumption
        consumption_r2 = ""
        
        if product:
            is_dt = product.get('etDt') == 'DT' or product.get('preisNT') is not None
            if is_dt:
                try:
                    total = float(total_consumption)
                    consumption_r1 = int(total * 0.7)
                    consumption_r2 = int(total * 0.3)
                    logger.info(f"⚖️ Split consumption: R1={consumption_r1}, R2={consumption_r2}")
                except ValueError:
                    logger.warning("Could not split consumption, using default")
                    
        return consumption_r1, consumption_r2



    async def _run_simulation(self, session):
        data = session["data"]
        
        # Guard: If we don't have consumption yet, ask for it
        if "consumption" not in data:
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return {
                 "reply": "Gerne! Für eine genaue Simulation benötige ich deinen Jahresverbrauch in kWh.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        token = sap_client.get_token()
        products = sap_client.get_products(token)
        
        # Match product
        product_id = data.get("product_id") # Check if we already have an ID (from SELECT_PRODUCT)
        product_name = data.get("product_name", "")
        logger.info(f"🕵️‍♀️ Matching product. ID: {product_id}, Name: '{product_name}'")
        
        if not product_id:
            # 1. Try exact match (case-insensitive)
            for p in products:
                p_name = p.get('bezeichnung') or p.get('name', '')
                if product_name.lower() == p_name.lower():
                    product_id = p.get('produktId')
                    product_name = p_name
                    break
            
            # 2. Try partial match with scoring
            if not product_id:
                best_match = None
                best_score = -1
                
                for p in products:
                    p_name = p.get('bezeichnung') or p.get('name', '')
                    p_lower = p_name.lower()
                    u_lower = product_name.lower()
                    
                    score = -1
                    
                    if u_lower == p_lower:
                        score = 1000 # Exact match
                    elif p_lower in u_lower:
                        # Product is substring of User Input (e.g. "INTENSIVE 12" in "I want INTENSIVE 12 please")
                        # We want the longest product name (most specific)
                        score = len(p_lower) * 10 
                    elif u_lower in p_lower:
                        # User Input is substring of Product (e.g. "INTENSIVE" in "INTENSIVE 12")
                        # We want the shortest product name (closest to input)
                        # Score should be higher for shorter names.
                        score = 100 - len(p_lower)
                    
                    if score > best_score:
                        best_score = score
                        best_match = p
                        logger.debug(f"Candidate: {p_name}, Score: {score}")
                
                if best_match:
                    product_id = best_match.get('produktId')
                    product_name = best_match.get('bezeichnung') or best_match.get('name')
                    logger.info(f"✅ Best match found: {product_name} (Score: {best_score})")

            if not product_id and products:
                # Default to first if absolutely no match found (fallback)
                product_id = products[0].get('produktId')
                product_name = products[0].get('bezeichnung')
            
        # Find full product object for UI and Logic
        full_product = next((p for p in products if p.get('produktId') == product_id), None)
        
        # Determine consumption split
        # Determine consumption split
        # If we have explicit R1/R2, use them. Otherwise use split logic.
        if data.get("consumption_r2"):
            consumption_r1 = data["consumption_r1"]
            consumption_r2 = data["consumption_r2"]
        else:
            consumption_r1, consumption_r2 = self._get_consumption_split(full_product, data["consumption"])

        sim_result = sap_client.simulate_price(token, consumption_r1, product_id, consumption_r2)
        
        session["state"] = STATE_SIMULATION_DONE
        data["product_id"] = product_id
        data["product_name"] = product_name
        
        product_ui_data = {}
        if full_product:
             base_price = float(full_product.get("grundpreis", 0.0))
             working_price = float(full_product.get("preisET_HT", 0.0)) * 100
             product_ui_data = {
                 "id": full_product.get("produktId"),
                 "name": full_product.get("bezeichnung") or full_product.get("name"),
                 "description": full_product.get("beschreibung", ""),
                 "isGreen": any(x in (full_product.get("bezeichnung") or "").lower() for x in ["oeko", "öko", "green", "day & night", "day and night"]) or full_product.get("oeko", False),
                 "basePrice": base_price,
                 "workingPrice": working_price,
                 "contractDuration": full_product.get("laufzeit", 12)
             }
        
        price = None
        if sim_result:
            # Try to get price from mock structure or real structure
            price = sim_result.get("total_price")
            
            # If not found, try real SAP structure
            if price is None:
                sim_data = sim_result.get("BillSimulation", {})
                net_amount = sim_data.get("NET_AMOUNT")
                if net_amount:
                    try:
                        price = float(net_amount)
                    except ValueError:
                        pass

        if price is None and full_product:
            # Fallback calculation to match UI
            try:
                bp = float(full_product.get("grundpreis", 0.0))
                wp = float(full_product.get("preisET_HT", 0.0))
                price = round(bp + (float(data["consumption"]) * wp), 2)
            except Exception as e:
                logger.warning(f"Fallback price calculation failed: {e}")
                price = None

        price_text = f"{price:.2f}€" if price is not None else "auf Anfrage"
        
        return {
            "reply": f"Der Tarif {product_name} kostet dich ca. {price_text} im Jahr. Möchtest du ein Angebot?",
            "state": STATE_SIMULATION_DONE,
            "ui_data": {
                "type": "simulation_result",
                "data": {"product": product_ui_data, "consumption": data["consumption"]}
            }
        }

    def _get_product_ui_data(self, products):
        products_data = []
        token = sap_client.get_token()
        
        logger.info(f"🎯 PROCESSING {len(products)} PRODUCTS FOR UI")
        
        for p in products:
             # Simulate price for 2500 kWh to get an estimate
             product_id = p.get("produktId")
             base_price = 0.0
             working_price = 0.0
             total_price = 0.0
             
             logger.info(f"🔍 Processing product: {p.get('bezeichnung')} (ID: {product_id})")
             
             if product_id:
                 # Determine consumption split for simulation (2500 kWh default)
                 sim_consumption_r1, sim_consumption_r2 = self._get_consumption_split(p, 2500)
                 
                 sim = sap_client.simulate_price(token, sim_consumption_r1, product_id, sim_consumption_r2)
                 if sim:
                     logger.info(f"✅ Simulation result keys: {sim.keys()}")
                     # Extract total from BillSimulation wrapper
                     sim_data = sim.get("BillSimulation", {})
                     total_price = float(sim_data.get("NET_AMOUNT", 0.0))
                     
                     # Extract components from product data directly (as seen in logs)
                     base_price = float(p.get("grundpreis", 0.0))
                     # Working price is in EUR/kWh, convert to Cents/kWh
                     working_price = float(p.get("preisET_HT", 0.0)) * 100
                     
                     logger.info(f"💵 Extracted prices - Base: {base_price}, Working: {working_price}, Total: {total_price}")
                 else:
                     logger.warning(f"⚠️ No simulation result for product {product_id}")
                     # Fallback to product data if simulation fails
                     base_price = float(p.get("grundpreis", 0.0))
                     working_price = float(p.get("preisET_HT", 0.0)) * 100

             products_data.append({
                 "id": p.get("produktId"),
                 "name": p.get("bezeichnung") or p.get("name"),
                 "description": p.get("beschreibung", ""),
                 "description": p.get("beschreibung", ""),
                 "isGreen": any(x in (p.get("bezeichnung") or "").lower() for x in ["oeko", "öko", "green", "day & night", "day and night"]) or p.get("oeko", False),
                 "basePrice": base_price,
                 "basePrice": base_price,
                 "workingPrice": working_price,
                 "totalPrice": total_price,
                 "contractDuration": p.get("laufzeit", 12)
             })
        
        logger.info(f"📤 SENDING TO FRONTEND: {products_data}")
        return {"type": "product_selection", "products": products_data}

chat_service = ChatService()
