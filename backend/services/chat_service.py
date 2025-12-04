import logging
import re
from datetime import datetime
from ..config import settings
from ..services.sap_client import SAPClient
from ..services.llm_service import LLMService
from ..services.email_service import EmailService
from ..services.product_service import ProductService
from ..services.simulation_service import SimulationService
from ..services.intent_service import IntentService

from ..session_manager import (
    session_manager,
    STATE_START,
    STATE_WAITING_FOR_CONSUMPTION,
    STATE_WAITING_FOR_PRODUCT_CHOICE,
    STATE_SIMULATION_DONE,
    STATE_WAITING_FOR_DATE,
    STATE_OFFER_CREATED,
    STATE_WAITING_FOR_DURATION,
    STATE_WAITING_FOR_TARIFF_TYPE,
    STATE_WAITING_FOR_EMAIL
)

logger = logging.getLogger(__name__)

# Instantiate services globally
sap_client = SAPClient()
llm_service = LLMService()
email_service = EmailService()

# Instantiate new services
product_service = ProductService(sap_client)
simulation_service = SimulationService(sap_client)
intent_service = IntentService(llm_service)

class ChatService:
    def __init__(self):
        self.product_service = product_service
        self.simulation_service = simulation_service
        self.intent_service = intent_service
        self.email_service = email_service
        self.sap_client = sap_client

    async def handle_message(self, user_id, text):
        session = session_manager.get_session(user_id)
        state = session["state"]
        data = session["data"]
        text_lower = text.lower()
        
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
            return await self._handle_select_product(session, text)

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
        elif state == STATE_WAITING_FOR_EMAIL:
            return await self._handle_email(session, text, user_id)
        
        # Fallback
        return {"reply": self.intent_service.generate_answer(text)}

    async def _handle_select_product(self, session, text):
        product_id = text.split(":", 1)[1]
        session["data"]["product_id"] = product_id
        
        # Find product name for the reply
        products = session["data"].get("products", [])
        if not products:
             products = await self.product_service.get_products()
             session["data"]["products"] = products
        
        product_name = next((p.get('bezeichnung') or p.get('name') for p in products if p.get('produktId') == product_id), "Gewählter Tarif")
        session["data"]["product_name"] = product_name
        
        # Check if we have consumption
        if not session["data"].get("consumption") and not session["data"].get("consumption_r1"):
             # Ask for consumption
             full_product = next((p for p in products if p.get('produktId') == product_id), None)
             is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
             
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

    async def _handle_start(self, session, text_lower, text):
        entities = self.intent_service.extract_entities(text)
        intent = entities.get("intent", "unknown")
        logger.info(f"🧠 Start Handler Intent: {intent}, Entities: {entities}")

        if intent in ["unknown", "question"] and "angebot" in text_lower:
             intent = "show_products"

        if intent == "show_products" or (intent == "confirmation" and any(x in text_lower for x in ["ja", "gerne", "ok"])):
            products = await self.product_service.get_products()
            if not products:
                return {"reply": "Entschuldigung, mein Tarifrechner macht gerade Pause. Bitte versuche es später."}
            
            session["state"] = STATE_WAITING_FOR_DURATION
            session["data"]["products"] = products
            
            return {
                "reply": "Gerne! Für welche Laufzeit interessierst du dich? (12 Monate, 24 Monate oder egal)",
                "state": STATE_WAITING_FOR_DURATION,
                "ui_data": {"type": "duration_selection"} 
            }

        if "consumption" in entities or intent == "selection":
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return await self._handle_consumption(session, text)

        if "household_size" in entities:
             size = int(entities["household_size"])
             estimated_consumption = 1500
             if size == 2: estimated_consumption = 2500
             elif size == 3: estimated_consumption = 3500
             elif size == 4: estimated_consumption = 4250
             elif size >= 5: estimated_consumption = 5000
             
             session["data"]["consumption"] = estimated_consumption
             session["data"]["consumption_r1"] = estimated_consumption
             session["data"]["consumption_r2"] = ""
             
             session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
             return {
                 "reply": f"Für {size} Personen rechne ich mit ca. {estimated_consumption} kWh. Welchen Tarif möchtest du wählen?",
                 "state": STATE_WAITING_FOR_PRODUCT_CHOICE,
                 "ui_data": await self.product_service.get_product_ui_data(session["data"].get("products", []), consumption=estimated_consumption, simulation_service=self.simulation_service)
             }

        if intent in ["question", "recommendation"] or any(x in text_lower for x in ["was", "wie", "wer", "hallo", "hi"]):
             context = {"state": "start", "instruction": "Du bist ein Energieberater. Beantworte die Frage kurz und frage dann: 'Möchtest du unsere Tarife sehen?'"}
             return {"reply": self.intent_service.generate_answer(text, context)}

        return {
             "reply": "Das habe ich nicht ganz verstanden. Möchtest du unsere Tarife sehen? (Antworte mit Ja)",
             "state": STATE_START
        }

    async def _handle_consumption(self, session, text):
        products = session["data"].get("products", [])
        p_id, p_name = self.product_service.find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            
            entities = self.intent_service.extract_entities(text)
            
            if not products:
                 products = await self.product_service.get_products()
            
            check_id = p_id or session["data"].get("product_id")
            full_product = next((p for p in products if p.get('produktId') == check_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if "household_size" in entities:
                 size = int(entities["household_size"])
                 estimated_consumption = 1500
                 if size == 2: estimated_consumption = 2500
                 elif size == 3: estimated_consumption = 3500
                 elif size == 4: estimated_consumption = 4250
                 elif size >= 5: estimated_consumption = 5000
                 
                 entities["consumption"] = estimated_consumption
                 
                 if is_dt:
                     r1 = int(estimated_consumption * 0.7)
                     r2 = estimated_consumption - r1
                     entities["consumption_r1"] = r1
                     entities["consumption_r2"] = r2

            if "consumption" in entities:
                if is_dt:
                     if "consumption_r1" in entities and "consumption_r2" in entities:
                         session["data"]["consumption"] = entities["consumption"]
                         session["data"]["consumption_r1"] = entities["consumption_r1"]
                         session["data"]["consumption_r2"] = entities["consumption_r2"]
                         return await self._run_simulation(session)
                     pass 
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
            
            msg = f"Gute Wahl! Der {p_name} ist ein toller Tarif. Um dir den genauen Preis zu sagen, brauche ich noch deinen Jahresverbrauch in kWh."
            if is_dt:
                msg = f"Gute Wahl! Der {p_name} ist ein Doppeltarif. Bitte nenne mir deinen Verbrauch für Tag (HT) und Nacht (NT) separat (z.B. 2000 HT und 1000 NT)."

            return {
                 "reply": msg,
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        entities = self.intent_service.extract_entities(text)
        
        if "household_size" in entities:
             size = int(entities["household_size"])
             estimated_consumption = 1500
             if size == 2: estimated_consumption = 2500
             elif size == 3: estimated_consumption = 3500
             elif size == 4: estimated_consumption = 4250
             elif size >= 5: estimated_consumption = 5000
             entities["consumption"] = estimated_consumption

        if "consumption" in entities:
            products = session["data"].get("products", [])
            if not products:
                 products = await self.product_service.get_products()
            
            check_id = session["data"].get("product_id")
            full_product = next((p for p in products if p.get('produktId') == check_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if is_dt:
                 msg = f"Für den Tarif {full_product.get('bezeichnung')} (Doppeltarif) benötige ich deinen Verbrauch für Tag (HT) und Nacht (NT) separat. Bitte nenne mir beide Werte."
                 return {
                     "reply": msg,
                     "state": STATE_WAITING_FOR_CONSUMPTION,
                     "ui_data": {"type": "consumption_input", "is_dt": True}
                 }

            session["data"]["consumption"] = entities["consumption"]
            session["data"]["consumption_r1"] = entities["consumption"]
            session["data"]["consumption_r2"] = ""
            
            if "product_name" in session["data"]:
                 return await self._run_simulation(session)

            if "product_name" in entities:
                session["data"]["product_name"] = entities["product_name"]
                return await self._run_simulation(session)
            
            session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
            return {
                "reply": f"Verstanden, {entities['consumption']} kWh. Welchen der Tarife möchtest du wählen?",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE,
                "ui_data": await self.product_service.get_product_ui_data(session["data"].get("products", []), consumption=entities['consumption'], simulation_service=self.simulation_service)
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
                "ui_data": await self.product_service.get_product_ui_data(session["data"].get("products", []), consumption=int(entities['consumption_r1']) + int(entities['consumption_r2']), simulation_service=self.simulation_service)
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
                 return {"reply": self.intent_service.generate_answer(text, context)}
            
            return {"reply": "Das habe ich nicht verstanden. Bitte nenne mir deinen Jahresverbrauch als Zahl (z.B. 3500)."}

    async def _handle_product_choice(self, session, text):
        products = session["data"].get("products", [])
        p_id, p_name = self.product_service.find_product_in_text(text, products)
        
        if p_id:
            session["data"]["product_id"] = p_id
            session["data"]["product_name"] = p_name
            
            full_product = next((p for p in products if p.get('produktId') == p_id), None)
            is_dt = full_product and (full_product.get('etDt') == 'DT' or full_product.get('preisNT') is not None)
            
            if is_dt and not session["data"].get("consumption_r2"):
                return {
                    "reply": f"Für den Tarif {p_name} (Doppeltarif) benötige ich deinen Verbrauch für Tag (HT) und Nacht (NT) separat. Bitte nenne mir beide Werte.",
                    "state": STATE_WAITING_FOR_CONSUMPTION,
                    "ui_data": {"type": "consumption_input", "is_dt": True}
                }
                
            return await self._run_simulation(session)

        extraction = self.intent_service.extract_entities(text)
        intent = extraction.get("intent", "unknown")
        data = session["data"]
        
        if intent == "correction" and "consumption" in extraction:
            data["consumption"] = extraction["consumption"]
            return {
                "reply": f"Okay, ich korrigiere den Verbrauch auf {data['consumption']} kWh. Welchen Tarif möchtest du wählen?",
                "ui_data": await self.product_service.get_product_ui_data(data.get("products", []), consumption=data['consumption'], simulation_service=self.simulation_service)
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
            reply = self.intent_service.generate_answer(text, context)
            for p in data.get("products", []):
                p_name = p.get("bezeichnung") or p.get("name", "")
                if p_name.upper() in reply.upper():
                    data["last_recommendation"] = p_name
                    break
            return {"reply": reply}

        elif intent == "confirmation" and "last_recommendation" in data:
            data["product_name"] = data["last_recommendation"]
            return await self._run_simulation(session)
            
        for p in data.get("products", []):
            p_name = p.get('bezeichnung') or p.get('name', '')
            if text.lower() in p_name.lower() or p_name.lower() in text.lower():
                data["product_name"] = p_name
                return await self._run_simulation(session)

        if any(x in text.lower() for x in ["tarif", "zeig", "liste", "angebot", "welche"]):
             return {
                "reply": "Hier sind unsere verfügbaren Tarife. Welchen möchtest du wählen?",
                "ui_data": await self.product_service.get_product_ui_data(data.get("products", []), consumption=data.get("consumption"), simulation_service=self.simulation_service)
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
        
        if self.intent_service.extract_entities(text).get("date"):
            session["state"] = STATE_WAITING_FOR_DATE
            return await self._handle_date(session, text, user_id)
            
        context = {"state": "simulation_done", "consumption": session["data"].get("consumption"), "product": session["data"].get("product_name")}
        return {"reply": self.intent_service.generate_answer(text, context)}

    async def _handle_date(self, session, text, user_id):
        entities = self.intent_service.extract_entities(text)
        if "date" in entities:
            start_date = entities["date"]
            date_obj = None
            try:
                date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            except ValueError:
                try:
                    date_obj = datetime.strptime(start_date.strip(), "%d.%m.%Y")
                except ValueError:
                    return {"reply": "Ungültiges Datumsformat. Bitte nutze TT.MM.JJJJ."}
            
            if date_obj < datetime.now():
                 return {"reply": "Das Datum liegt in der Vergangenheit. Bitte nenne ein Datum in der Zukunft."}
            
            start_date_iso = date_obj.strftime("%Y-%m-%d")
            session["data"]["start_date"] = start_date_iso
            
            if "@" in user_id:
                return await self._handle_email(session, user_id, user_id)
            
            session["state"] = STATE_WAITING_FOR_EMAIL
            return {
                "reply": "Perfekt! 📧 An welche E-Mail-Adresse darf ich dir das Angebot senden?",
                "state": STATE_WAITING_FOR_EMAIL
            }
        
        return {"reply": "Ich konnte kein Datum erkennen. Bitte nenne ein Datum (z.B. 01.01.2026)."}

    async def _handle_email(self, session, text, user_id):
        email = text.strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return {"reply": "Das sieht nicht wie eine gültige E-Mail-Adresse aus. Bitte versuche es noch einmal."}
            
        session["data"]["email"] = email
        
        try:
            token = await self.sap_client.get_token()
            product_id = session["data"].get("product_id", "INT12_DEMO_PROD")
            
            consumption = session["data"].get("consumption", "2500")
            
            products = session["data"].get("products", [])
            if not products:
                    products = await self.product_service.get_products()
            
            full_product = next((p for p in products if p.get('produktId') == product_id), None)
            
            consumption_r1, consumption_r2 = self.simulation_service.get_consumption_split(full_product, consumption)

            offer = await self.sap_client.create_offer(token, product_id, session["data"]["start_date"], consumption_r1, consumption_r2, {"user_id": user_id, "email": email})
            error_msg = None
            
            if offer:
                logger.info(f"✅ OFFER RESPONSE: {offer}")
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
            
                product_name = session["data"].get("product_name", "Stromtarif")
                
                price_text = session["data"].get("simulated_price")
                if not price_text:
                    price_text = "auf Anfrage"
                elif isinstance(price_text, (float, int)):
                    price_text = f"{price_text:.2f}€"
                
                email_sent = await self.email_service.send_offer_email(
                    to_email=email,
                    offer_id=offer_id,
                    product_name=product_name,
                    consumption=str(consumption),
                    price=price_text
                )

                session_manager.reset_session(user_id)
                session["state"] = STATE_START
                session["data"] = {}
                
                reply_text = f"Geschafft! 🎉 Hier ist dein Angebot: {offer_id}\n\nIch habe dir die Details an **{email}** gesendet."
                if not email_sent:
                    reply_text += "\n(Der E-Mail-Versand hat leider nicht geklappt, aber das Angebot ist im System gespeichert.)"

                return {
                    "reply": reply_text,
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
        return {"reply": self.intent_service.generate_answer(text, context)}

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
        
        context = {"state": "waiting_for_duration", "instruction": "Der User soll eine Laufzeit (12/24 Monate) wählen. Beantworte seine Frage und erinnere ihn dann an die Auswahl."}
        return {"reply": self.intent_service.generate_answer(text, context)}

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
            
            all_products = session["data"].get("products", [])
            filtered_products = []
            
            filter_duration = session["data"].get("filter_duration")
            
            for p in all_products:
                if filter_duration != "egal":
                    if int(p.get("laufzeit", 12)) != int(filter_duration):
                        continue
                
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
                    "state": STATE_WAITING_FOR_DURATION, 
                    "ui_data": {"type": "duration_selection"} 
                }

            session["state"] = STATE_WAITING_FOR_PRODUCT_CHOICE
            
            product_lines = [f"- {p.get('bezeichnung') or p.get('name', 'Unbekannt')}" for p in filtered_products]
            product_list = "\n".join(product_lines)
            
            return {
                "reply": f"Hier sind die passenden Tarife:\n\n{product_list}\n\nWelchen möchtest du wählen? (Oder nenne mir deinen Verbrauch für eine Berechnung)",
                "state": STATE_WAITING_FOR_PRODUCT_CHOICE, 
                "ui_data": await self.product_service.get_product_ui_data(filtered_products, consumption=session["data"].get("consumption"), simulation_service=self.simulation_service)
            }
            
        context = {"state": "waiting_for_tariff_type", "instruction": "Der User soll einen Tariftyp (Einzel/Doppel) wählen. Beantworte seine Frage und erinnere ihn dann an die Auswahl."}
        return {"reply": self.intent_service.generate_answer(text, context)}

    async def _run_simulation(self, session):
        data = session["data"]
        
        if "consumption" not in data:
             session["state"] = STATE_WAITING_FOR_CONSUMPTION
             return {
                 "reply": "Gerne! Für eine genaue Simulation benötige ich deinen Jahresverbrauch in kWh.",
                 "state": STATE_WAITING_FOR_CONSUMPTION,
                 "ui_data": {"type": "consumption_input"}
             }

        products = session["data"].get("products", [])
        if not products:
             products = await self.product_service.get_products()
        
        product_id = data.get("product_id")
        product_name = data.get("product_name", "")
        
        if not product_id:
            product_id, product_name = self.product_service.find_product_in_text(product_name, products)
            if not product_id and products:
                product_id = products[0].get('produktId')
                product_name = products[0].get('bezeichnung')
            
        full_product = next((p for p in products if p.get('produktId') == product_id), None)
        
        if data.get("consumption_r2"):
            consumption_r1 = data["consumption_r1"]
            consumption_r2 = data["consumption_r2"]
        else:
            consumption_r1, consumption_r2 = self.simulation_service.get_consumption_split(full_product, data["consumption"])

        sim_result, _, _ = await self.simulation_service.simulate_price(product_id, data["consumption"], product=full_product, consumption_r1=consumption_r1, consumption_r2=consumption_r2)
        
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
                bp = float(full_product.get("grundpreis", 0.0))
                wp = float(full_product.get("preisET_HT", 0.0))
                price = round(bp + (float(data["consumption"]) * wp), 2)
            except Exception as e:
                logger.warning(f"Fallback price calculation failed: {e}")
                price = None
        
        if price is not None:
            data["simulated_price"] = price

        price_text = f"{price:.2f}€" if price is not None else "auf Anfrage"
        
        return {
            "reply": f"Der Tarif {product_name} kostet dich ca. {price_text} im Jahr. Möchtest du ein Angebot?",
            "state": STATE_SIMULATION_DONE,
            "ui_data": {
                "type": "simulation_result",
                "data": {"product": product_ui_data, "consumption": data["consumption"]}
            }
        }

chat_service = ChatService()
