import re
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model = None
        self.enabled = False
        self.keys = [k for k in [settings.GEMINI_API_KEY, settings.GEMINI_API_KEY_2] if k]
        self.current_key_index = 0
        self._initialize()

    def _initialize(self):
        if not self.keys or settings.MOCK_LLM:
            logger.warning("Gemini API key not found or Mock Mode enabled. Using Mock LLM.")
            self.enabled = False
            return

        try:
            import google.generativeai as genai
            current_key = self.keys[self.current_key_index]
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction="Du bist Sparky, ein freundlicher, moderner Energieberater-Bot. Antworte immer kurz (max. 2 Sätze). Nutze Emojis ⚡. Formatiere wichtige Begriffe fett (**Wort**). Sei hilfsbereit aber locker."
            )
            self.enabled = True
            logger.info(f"✅ Gemini AI enabled ({settings.GEMINI_MODEL}) using Key #{self.current_key_index + 1}!")
        except Exception as e:
            logger.error(f"⚠️ Error initializing Gemini with Key #{self.current_key_index + 1}: {e}")
            self._rotate_key()

    def _rotate_key(self):
        if len(self.keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)
            logger.warning(f"🔄 Switching to Gemini Key #{self.current_key_index + 1}...")
            self._initialize()
            return True
        return False

    def generate_answer(self, prompt, context_data=None):
        """
        Generates an answer using Gemini LLM.
        """
        if not self.enabled:
            return "Fehler: Gemini API Key fehlt. Bitte konfiguriere GEMINI_API_KEY in der .env Datei."

        try:
            system_prompt = """
            Du bist ein freundlicher und professioneller Vertriebsmitarbeiter der Firma INTENSE AG.
            Deine Aufgabe ist es, Kunden zu Stromtarifen zu beraten.
            
            REGELN:
            1. Du darfst KEINE Preise erfinden. Wenn der Kunde nach einem Preis fragt, sage, dass du erst den Verbrauch wissen musst, um die Simulation zu starten.
            2. Sei kurz und prägnant. Telegram-Nachrichten sollten nicht länger als 3 Sätze sein.
            3. Wenn der Kunde "Angebot" sagt, frage nach dem gewünschten Startdatum, falls es noch fehlt.
            4. Deine Tonalität ist hilfreich, höflich und "Du"-Form.
            
            WICHTIG:
            Wenn du Daten vom Nutzer erhalten hast (z.B. Verbrauch oder Datum), wiederhole diese kurz zur Bestätigung.
            """
            
            full_prompt = f"{system_prompt}\n\n"
            if context_data:
                if "instruction" in context_data:
                    full_prompt += f"WICHTIG: {context_data['instruction']}\n\n"
                full_prompt += f"Kontext: {json.dumps(context_data, ensure_ascii=False)}\n\n"
            full_prompt += f"Kunde: {prompt}\n\nDeine Antwort:"
            
            # Retry loop for fallback
            max_retries = len(self.keys)
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(full_prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"Gemini API Error (Key #{self.current_key_index + 1}): {e}")
                    if "429" in str(e) or "403" in str(e):
                        if self._rotate_key():
                            continue
                    break # Stop if rotation not possible or other error
            
            return "Entschuldigung, ich hatte kurz technische Probleme. Kannst du das bitte wiederholen?"
        except Exception as e:
            logger.error(f"Critical Gemini Error: {e}")
            return "Entschuldigung, ich hatte kurz technische Probleme. Kannst du das bitte wiederholen?"

    def extract_entities(self, text):
        """
        Extracts entities (consumption, product choice, date) from text using Gemini.
        Falls back to Regex only if Gemini fails.
        """
        result = {}
        
        if self.enabled:
            try:
                prompt = f"""
                Analysiere den Text und extrahiere Daten sowie die Absicht (Intent) als JSON:
                
                1. intent (String):
                   - "selection": User wählt ein Produkt oder nennt Daten (Verbrauch, Datum).
                   - "recommendation": User fragt nach Empfehlung/Hilfe.
                   - "question": User stellt eine allgemeine Frage.
                   - "correction": User korrigiert eine vorherige Eingabe.
                   - "confirmation": User stimmt zu.
                   - "rejection": User lehnt ab.
                
                2. Daten (falls vorhanden):
                   - consumption (Zahl in kWh, z.B. 3500) -> Falls nur EINE Zahl genannt wird.
                   - consumption_r1 (Zahl in kWh) -> Tagstrom / HT / erster Wert.
                   - consumption_r2 (Zahl in kWh) -> Nachtstrom / NT / zweiter Wert.
                   - date (Datum im Format YYYY-MM-DD)
                   - product_name (Name des Tarifs)
                
                Text: "{text}"
                
                Antworte NUR mit dem JSON-Objekt.
                """
                response = self.model.generate_content(prompt)
                cleaned_text = response.text.strip()
                
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
                    
                result = json.loads(cleaned_text)
                result = json.loads(cleaned_text)
            except Exception as e:
                logger.error(f"LLM Extraction Error (Key #{self.current_key_index + 1}): {e}")
                if "429" in str(e) or "403" in str(e):
                    if self._rotate_key():
                        # Retry once with new key (recursive call could be dangerous, just pass for now or simple retry logic)
                        # For simplicity in extraction, we just log and fall back to regex if rotation happens here
                        # Ideally we would retry the extraction, but let's rely on regex fallback for robustness
                        pass
                pass

        # Fallback Logic (Always runs if key missing or LLM disabled)
        if "consumption" not in result and "consumption_r1" not in result:
            # Explicit "Verbrauch: X" pattern
            explicit_match = re.search(r'Verbrauch[:\s]+(\d{3,5})', text, re.IGNORECASE)
            if explicit_match:
                result['consumption'] = int(explicit_match.group(1))
            else:
                # Look for two numbers for HT/NT
                two_nums = re.findall(r'\b(\d{3,5})\b', text)
                if len(two_nums) >= 2:
                    result['consumption_r1'] = int(two_nums[0])
                    result['consumption_r2'] = int(two_nums[1])
                elif len(two_nums) == 1:
                    result['consumption'] = int(two_nums[0])

        if "date" not in result:
            date_match = re.search(r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b', text)
            if date_match:
                d, m, y = date_match.group(1).split('.')
                result['date'] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            else:
                iso_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
                if iso_match:
                    result['date'] = iso_match.group(1)

        if "product_name" not in result:
            text_lower = text.lower()
            if "green" in text_lower:
                result['product_name'] = "Green Energy"
            elif "intense" in text_lower or "intensive" in text_lower:
                result['product_name'] = "INTENSIVE"

        return result

# Singleton instance
llm_service = LLMService()
