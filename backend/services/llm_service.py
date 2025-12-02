import re
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.gemini_model = None
        self.deepseek_client = None
        self.enabled = False
        self._initialize()

    def _initialize(self):
        if settings.MOCK_LLM:
            logger.warning("LLM Mock Mode enabled.")
            self.enabled = False
            return

        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "deepseek":
            self._init_deepseek()
        else:
            logger.error(f"Unknown LLM Provider: {self.provider}")
            self.enabled = False

    def _init_gemini(self):
        try:
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set")
                
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction="Du bist Sparky, ein freundlicher, moderner Energieberater-Bot. Antworte immer kurz (max. 2 Sätze). Nutze Emojis ⚡. Formatiere wichtige Begriffe fett (**Wort**). Sei hilfsbereit aber locker."
            )
            self.enabled = True
            logger.info(f"✅ Gemini AI enabled ({settings.GEMINI_MODEL})!")
        except Exception as e:
            logger.error(f"⚠️ Error initializing Gemini: {e}")
            self.enabled = False

    def _init_deepseek(self):
        try:
            from openai import OpenAI
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY not set")
                
            self.deepseek_client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
            self.enabled = True
            logger.info(f"✅ DeepSeek AI enabled ({settings.DEEPSEEK_MODEL})!")
        except Exception as e:
            logger.error(f"⚠️ Error initializing DeepSeek: {e}")
            self.enabled = False

    def generate_answer(self, prompt, context_data=None):
        """
        Generates an answer using the configured LLM provider.
        """
        if not self.enabled:
            return "Ich bin im Offline-Modus. Bitte nutze die Buttons oder schreibe 'Start', um neu zu beginnen."

        system_prompt = """
        Du bist ein freundlicher und professioneller Vertriebsmitarbeiter der Firma INTENSE AG.
        Deine Aufgabe ist es, Kunden zu Stromtarifen zu beraten.
        
        REGELN:
        1. Du darfst KEINE Preise erfinden. Wenn der Kunde nach einem Preis fragt, sage, dass du erst den Verbrauch wissen musst, um die Simulation zu starten.
        2. Sei kurz und prägnant. Telegram-Nachrichten sollten nicht länger als 3 Sätze sein.
        3. Wenn der Kunde "Angebot" sagt, frage nach dem gewünschten Startdatum, falls es noch fehlt.
        4. Deine Tonalität ist hilfreich, höflich und "Du"-Form.
        5. Nutze Emojis ⚡.
        
        WICHTIG:
        Wenn du Daten vom Nutzer erhalten hast (z.B. Verbrauch oder Datum), wiederhole diese kurz zur Bestätigung.
        """
        
        full_prompt = f"{system_prompt}\n\n"
        if context_data:
            if "instruction" in context_data:
                full_prompt += f"WICHTIG: {context_data['instruction']}\n\n"
            full_prompt += f"Kontext: {json.dumps(context_data, ensure_ascii=False)}\n\n"
        full_prompt += f"Kunde: {prompt}\n\nDeine Antwort:"

        if self.provider == "gemini":
            return self._generate_gemini(full_prompt)
        elif self.provider == "deepseek":
            return self._generate_deepseek(system_prompt, full_prompt) # DeepSeek handles system prompt differently in messages
        
        return "Fehler: Kein LLM Provider konfiguriert."

    def _generate_gemini(self, prompt):
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return self._handle_error(e)

    def _generate_deepseek(self, system_prompt, full_user_prompt):
        try:
            response = self.deepseek_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_user_prompt} 
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, e):
        error_msg = str(e)
        logger.error(f"LLM API Error ({self.provider}): {error_msg}")
        
        if "429" in error_msg:
            return "Entschuldigung, ich bin gerade etwas überlastet (zu viele Anfragen). Bitte versuche es in einer Minute noch einmal. ⏳"
            
        return "Entschuldigung, ich hatte kurz technische Probleme. Kannst du das bitte wiederholen?"

    def extract_entities(self, text):
        """
        Extracts entities (consumption, product choice, date) from text.
        """
        result = {}
        
        if self.enabled:
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
            
            try:
                cleaned_text = ""
                if self.provider == "gemini":
                    response = self.gemini_model.generate_content(prompt)
                    cleaned_text = response.text.strip()
                elif self.provider == "deepseek":
                    response = self.deepseek_client.chat.completions.create(
                        model=settings.DEEPSEEK_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a data extraction assistant. Output only JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0
                    )
                    cleaned_text = response.choices[0].message.content.strip()

                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
                    
                result = json.loads(cleaned_text)
            except Exception as e:
                logger.error(f"LLM Extraction Error ({self.provider}): {e}")
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
