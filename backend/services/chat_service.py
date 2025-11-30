import logging
import re
import asyncio
from datetime import datetime
from ..config import settings
from ..services.sap_client import sap_client
from ..services.llm_service import LLMService
from ..utils.text_matching import find_product_in_text

from ..session_manager import (
    SessionManager,
    STATE_START,
    STATE_WAITING_FOR_CONSUMPTION,
    STATE_WAITING_FOR_PRODUCT_CHOICE,
    STATE_SIMULATION_DONE,
    STATE_WAITING_FOR_DATE,
    STATE_OFFER_CREATED,
    STATE_CONFIRM_RESET
)

logger = logging.getLogger(__name__)

llm_service = LLMService()
session_manager = SessionManager()

class ChatService:
    def _safe_float(self, value):
        """Helper to safely convert values to float, handling commas and None."""
        if value is None:
            return 0.0
        try:
            if isinstance(value, (int, float)):
                return float(value)
            # Handle German format (1.200,50 -> 1200.50)
            val_str = str(value).replace('.', '').replace(',', '.')
            return float(val_str)
        except (ValueError, TypeError):
            return 0.0

    async def handle_message(self, user_id, text):
        session = session_manager.get_session(user_id)
        state = session["state"]
        data = session["data"]
        text_lower = text.lower()
        
        # Global Intents
        if "reset" in text_lower or "start" in text_lower:
            if state == STATE_START:
                 return await self._handle_start(session, text_lower, text)
            
            session["state"] = STATE_CONFIRM_RESET
            return {
                "reply": "Möchtest du den aktuellen Chat wirklich beenden und neu starten?",
                "quick_replies": ["Ja, Neustart", "Nein, weiter"]
            }

        # Direct Product Selection (Bypass LLM)
        if text.startswith("SELECT_PRODUCT:"):
            product_id = text.split(":", 1)[1]
            session["data"]["product_id"] = product_id
            
            products = session["data"].get("products", [])
            if not products:
                 token = await sap_client.get_token()
                 products = await sap_client.get_products(token)
                 session["data"]["products"] = products
            
            product_name = next((p.get('bezeichnung') or p.get('name') for p in products if p.get('produktId') == product_id), "Gewählter Tarif")
            session["data"]["product_name"] = product_name
            
            if "consumption" in session["data"]:
                return await self._run_simulation(session)
            else:
                session["state"] = STATE_WAITING_FOR_CONSUMPTION
                return {
                    "reply": f"Gute Wahl! Der {product_name} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh.",
                    "state": STATE_WAITING_FOR_CONSUMPTION,
                    "ui_data": {"type": "consumption_input"}
                }

        # State Machine
        if state == STATE_START:
            return await self._handle_start(session, text_lower, text)
        elif state == STATE_CONFIRM_RESET:
            return await self._handle_confirm_reset(session, text_lower, user_id)
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
        
        # Fallback
        return {"reply": llm_service.generate_answer(text)}

    async def _handle_confirm_reset(self, session, text_lower, user_id):
        if any(x in text_lower for x in ["ja", "yes", "neustart", "reset", "ok"]):
            session_manager.reset_session(user_id)
            return {"reply": "Alles zurückgesetzt. Hallo! Ich bin Sparky. Sag 'Hallo' um zu starten."}
        else:
            return {"reply": "Okay, wir machen weiter. (Schreibe 'Start' wenn du es dir anders überlegst).", "state": STATE_START}

    async def _handle_start(self, session, text_lower, text):
        if any(x in text_lower for x in ["tarif", "produkte", "angebot", "zeig", "ja", "gerne", "ok", "sicher", "klar", "mach"]):
            token = await sap_client.get_token()
            products = await sap_client.get_products(token)
            if not products:
                return {"reply": "Entschuldigung, mein Tarifrechner macht gerade Pause. Bitte versuche es später."}
            
            product_lines = [f"- {p.get('bezeichnung') or p.get('name', 'Unbekannt')}" for p in products]
            product_list = "\n".join(product_lines)
            
            session["state"] = STATE_WAITING_FOR_CONSUMPTION
            session["data"]["products"] = products
            
            ui_data = await self._get_product_ui_data(products)
            
            return {
                "reply": f"Hier sind unsere aktuellen Tarife:\n\n{product_list}\n\nHast du Fragen dazu oder soll ich direkt die Kosten für dich berechnen? (Dafür bräuchte ich deinen Jahresverbrauch)",
                "state": STATE_WAITING_FOR_CONSUMPTION,
                "ui_data": ui_data
            }

        elif any(x in text_lower for x in ["hallo", "hi", "hey", "start"]):
             return {
                 "reply": "**Hallo!** 👋 Ich bin **Sparky**, dein Energieberater der INTENSE AG.\n\nMöchtest du unsere Tarife sehen, eine Simulation starten oder hast du eine Frage?",
                 "state": STATE_START,
                 "quick_replies": ["Tarife anzeigen", "Simulation starten", "Was kannst du?"]
             }
            
        elif any(x in text_lower for x in ["simulat", "berechnen", "rechnen", "kosten"]):
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return {
                 "reply": "Gerne! Für eine genaue Simulation benötige ich deinen Jahresverbrauch.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }
             
        entities = llm_service.extract_entities(text)
        if "consumption" in entities:
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return await self._handle_consumption(session, text)

        else:
            context = {"state": "start", "instruction": "Du bist ein Energieberater. Beantworte die Frage kurz und frage dann: 'Möchtest du unsere Tarife sehen?'"}
            return {"reply": llm_service.generate_answer(text, context)}

    async def _handle_consumption(self, session, text):
        products = session["data"].get("products", [])
        p_id, p_name = find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            
            entities = llm_service.extract_entities(text)
            if "consumption" in entities:
                session["data"]["consumption"] = entities["consumption"]
                return await self._run_simulation(session)
            
            return {
                 "reply": f"Gute Wahl! Der {p_name} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        entities = llm_service.extract_entities(text)
        
        if "consumption" not in entities:
            numbers = re.findall(r'\b\d{3,5}\b', text)
            if numbers:
                entities["consumption"] = numbers[0]
        
        if "consumption" in entities:
            session["data"]["consumption"] = entities["consumption"]
            
            if "product_name" in session["data"]:
                 return await self._run_simulation(session)

            if "product_name" in entities:
                session["data"]["product_name"] = entities["product_name"]
                return await self._run_simulation(session)
            
            session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
            ui_data = await self._get_product_ui_data(session["data"].get("products", []))
            return {
                "reply": f"Verstanden, **{entities['consumption']} kWh**. Welchen der Tarife möchtest du wählen?",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE,
                "ui_data": ui_data
            }
        
        elif "product_name" in entities:
             session["data"]["product_name"] = entities["product_name"]
             return {
                 "reply": f"Gute Wahl! Der {entities['product_name']} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        else:
            text_lower = text.lower()
            if "angebot" in text_lower:
                return {"reply": "Gerne erstelle ich dir ein Angebot! Dafür brauche ich zunächst deinen Jahresverbrauch in kWh."}
            elif any(word in text_lower for word in ["was", "wie", "warum", "welche", "?", "erkläre"]):
                 context = {"state": "waiting_for_consumption", "products": session["data"].get("products", [])}
                 return {"reply": llm_service.generate_answer(text, context)}
            
            return {"reply": "Das habe ich nicht verstanden. Bitte nenne mir deinen Jahresverbrauch als Zahl (z.B. 3500)."}

    async def _handle_product_choice(self, session, text):
        products = session["data"].get("products", [])
        p_id, p_name = find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            return await self._run_simulation(session)

        extraction = llm_service.extract_entities(text)
        intent = extraction.get("intent", "unknown")
        data = session["data"]
        
        if intent == "correction" and "consumption" in extraction:
            data["consumption"] = extraction["consumption"]
            ui_data = await self._get_product_ui_data(data.get("products", []))
            return {
                "reply": f"Okay, ich korrigiere den Verbrauch auf **{data['consumption']} kWh**. Welchen Tarif möchtest du wählen?",
                "ui_data": ui_data
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
            return {"reply": reply}
            
        elif intent == "confirmation" and "last_recommendation" in data:
            data["product_name"] = data["last_recommendation"]
            return await self._run_simulation(session)
            
        if any(x in text.lower() for x in ["tarif", "zeig", "liste", "angebot", "welche"]):
             ui_data = await self._get_product_ui_data(data.get("products", []))
             return {
                "reply": "Hier sind unsere verfügbaren Tarife. Welchen möchtest du wählen?",
                "ui_data": ui_data
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
        
        if llm_service.extract_entities(text).get("date"):
            session["state"] = STATE_WAITING_FOR_DATE
            return await self._handle_date(session, text, user_id)
            
        context = {"state": "simulation_done", "consumption": session["data"].get("consumption"), "product": session["data"].get("product_name")}
        return {"reply": llm_service.generate_answer(text, context)}

    async def _handle_date(self, session, text, user_id):
        entities = llm_service.extract_entities(text)
        if "date" in entities:
            start_date = entities["date"]
            try:
                date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                if date_obj < datetime.now():
                     return {"reply": "Das Datum liegt in der Vergangenheit. Bitte nenne ein Datum in der Zukunft."}
                
                session["data"]["start_date"] = start_date
                token = await sap_client.get_token()
                product_id = session["data"].get("product_id", "INT12_DEMO_PROD")
                
                consumption = session["data"].get("consumption", "2500")
                
                products = session["data"].get("products", [])
                if not products:
                     products = await sap_client.get_products(token)
                
                full_product = next((p for p in products if p.get('produktId') == product_id), None)
                
                consumption_r1, consumption_r2 = self._get_consumption_split(full_product, consumption)

                offer = await sap_client.create_offer(token, product_id, start_date, consumption_r1, consumption_r2, {"user_id": user_id})
                if offer:
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
                        
                    offer_id = offer_data.get("displayId") or offer_data.get("ObjectID") or offer_data.get("offer_id") or offer_data.get("ID") or offer_data.get("Angebotsnummer") or offer.get("offer_id")
                    
                    product_name = session["data"].get("product_name", "Stromtarif")
                    
                    session_manager.reset_session(user_id)
                    session["state"] = STATE_START
                    session["data"] = {}
                    
                    return {
                        "reply": f"Geschafft! 🎉 Hier ist dein Angebot: **{offer_id}**\n\nIn einem echten Szenario würdest du diese Nummer verwenden, um den Vertrag zu unterschreiben oder sie beim Support anzugeben.",
                        "state": STATE_OFFER_CREATED,
                        "ui_data": {
                            "type": "offer_success", 
                            "offer_id": offer_id,
                            "product_name": product_name
                        }
                    }
                else:
                    session_manager.reset_session(user_id)
                    return {"reply": "Es gab einen Fehler bei der Angebotserstellung (SAP Systemfehler). Bitte versuche es später noch einmal."}
            except ValueError:
                 return {"reply": "Ungültiges Datumsformat. Bitte nutze TT.MM.JJJJ."}
        
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
                except ValueError:
                    pass
                    
        return consumption_r1, consumption_r2

    async def _run_simulation(self, session):
        data = session["data"]
        token = await sap_client.get_token()
        products = await sap_client.get_products(token)
        
        product_id = data.get("product_id")
        product_name = data.get("product_name", "")
        
        if not product_id:
            # Try exact match
            for p in products:
                p_name = p.get('bezeichnung') or p.get('name', '')
                if product_name.lower() == p_name.lower():
                    product_id = p.get('produktId')
                    product_name = p_name
                    break
            
            # Try robust match if still no ID
            if not product_id:
                p_id, p_name = find_product_in_text(product_name, products)
                if p_id:
                    product_id = p_id
                    product_name = p_name

            if not product_id and products:
                product_id = products[0].get('produktId')
                product_name = products[0].get('bezeichnung')
            
        full_product = next((p for p in products if p.get('produktId') == product_id), None)
        consumption_r1, consumption_r2 = self._get_consumption_split(full_product, data["consumption"])

        sim_result = await sap_client.simulate_price(token, consumption_r1, product_id, consumption_r2)
        
        session["state"] = STATE_SIMULATION_DONE
        data["product_id"] = product_id
        data["product_name"] = product_name
        
        product_ui_data = {}
        if full_product:
             base_price = self._safe_float(full_product.get("grundpreis"))
             working_price = self._safe_float(full_product.get("preisET_HT")) * 100
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
            price = sim_result.get("total_price")
            if price is None:
                sim_data = sim_result.get("BillSimulation", {})
                net_amount = sim_data.get("NET_AMOUNT")
                if net_amount:
                    try:
                        price = float(net_amount)
                    except ValueError:
                        pass

        if price is None and full_product:
            try:
                bp = self._safe_float(full_product.get("grundpreis"))
                wp_ht = self._safe_float(full_product.get("preisET_HT"))
                
                if full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None:
                    wp_nt = self._safe_float(full_product.get("preisNT"))
                    # Recalculate split locally if needed, or use what we sent
                    c_r1, c_r2 = self._get_consumption_split(full_product, data["consumption"])
                    price = round(bp + (c_r1 * wp_ht) + (c_r2 * wp_nt), 2)
                else:
                    price = round(bp + (float(data["consumption"]) * wp_ht), 2)
            except Exception:
                price = None

        total_price = price if price is not None else 0.0
        monthly_price = total_price / 12 if total_price > 0 else 0.0
        
        monthly_str = f"{monthly_price:.2f}".replace('.', ',')
        yearly_str = f"{total_price:.2f}".replace('.', ',')
        
        response_text = (
            f"📊 **Dein Ergebnis für {product_name}:**\n\n"
            f"📅 Monatlich: **{monthly_str} €**\n"
            f"🗓️ Jährlich: **{yearly_str} €**\n\n"
            f"Soll ich das Angebot für dich erstellen?"
        )
        
        return {
            "reply": response_text,
            "state": STATE_SIMULATION_DONE,
            "ui_data": {
                "type": "simulation_result",
                "data": {"product": product_ui_data, "consumption": data["consumption"]}
            }
        }

    async def _get_product_ui_data(self, products):
        products_data = []
        token = await sap_client.get_token()
        
        # Parallelize simulations? For now, keep it sequential but async to avoid overwhelming SAP
        # Or better: use asyncio.gather if we trust the API rate limit
        
        for p in products:
             product_id = p.get("produktId")
             base_price = 0.0
             working_price = 0.0
             total_price = 0.0
             
             if product_id:
                 sim_consumption_r1, sim_consumption_r2 = self._get_consumption_split(p, 2500)
                 sim = await sap_client.simulate_price(token, sim_consumption_r1, product_id, sim_consumption_r2)
                 
                 if sim:
                     sim_data = sim.get("BillSimulation", {})
                     total_price = float(sim_data.get("NET_AMOUNT", 0.0))
                     base_price = self._safe_float(p.get("grundpreis"))
                     working_price = self._safe_float(p.get("preisET_HT")) * 100
                 else:
                     base_price = self._safe_float(p.get("grundpreis"))
                     working_price = self._safe_float(p.get("preisET_HT")) * 100

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
        
        return {"type": "product_selection", "products": products_data}

chat_service = ChatService()
