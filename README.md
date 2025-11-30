# INTENSE Energieberater - Multi-Channel Chatbot

Ein intelligenter Chatbot für die Energietarifberatung, entwickelt als Semester-Projekt für INTENSE AG.

> **📘 Documentation**
>
> Detailed technical documentation (Backend, API, Channels) is available in the [docs/](docs/README.md) directory.


## 🎯 Projektübersicht

Dieser Chatbot ermöglicht Kunden die Beratung zu Energietarifen über mehrere Kanäle (Multi-Channel):
- **Web Portal** (HTML/JavaScript Interface)
- **Telegram Bot** (@SparkyBerater_bot)
- **E-Mail** (Optional, noch nicht implementiert)

### Hauptfunktionen

1. **Intelligente Tarifberatung**: Zeigt verfügbare Tarife basierend auf SAP-Produktdaten
2. **Preissimulation**: Berechnet Kosten basierend auf Jahresverbrauch
3. **Angebotserstellung**: Erstellt automatisch Angebote im SAP Sales & Service Cloud

## 📁 Projektstruktur

```
CBI/
├── main.py                 # FastAPI Backend mit State Machine
├── sap_client.py          # SAP Integration (Auth, Products, Simulation, Offer)
├── llm_service.py         # LLM Service mit Entity Extraction
├── telegram_bot.py        # Telegram Bot Interface
├── index.html             # Web Chat Interface
├── requirements.txt       # Python Dependencies
├── .env                   # Konfiguration (Credentials)
├── start_backend.sh       # Backend starten
├── start_telegram.sh      # Telegram Bot starten
└── run_all.sh            # Alle Tests ausführen
```

## 🚀 Schnellstart

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. Backend & Web Portal starten

```bash
./start_backend.sh
```

Dann öffnen: **http://localhost:8000**

### 3. Telegram Bot starten (in neuem Terminal)

```bash
./start_telegram.sh
```

Dann chatten mit: **@SparkyBerater_bot**

## 🧪 Tests ausführen

```bash
./run_all.sh
```

Dies führt zwei Tests aus:
- **Setup Test**: Verifiziert SAP Client, LLM Service, Backend
- **Flow Test**: Simuliert kompletten Gesprächsablauf

## 🔑 Konfiguration

Die Datei `.env` enthält alle Credentials:

```env
# SAP Credentials (von INTENSE AG bereitgestellt)
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret

# Google Gemini API (Optional, für echte KI-Antworten)
# Hol dir deinen Key hier: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key

# Telegram (bereits konfiguriert)
TELEGRAM_BOT_TOKEN=8251533467:AAGAgMHqoPuHbDGZLi3ZRY_qZHfMF7fWWPQ
```

**Wichtig**: Bis die echten SAP-Credentials eingetragen sind, verwendet das System Mock-Daten.

## 💬 Gesprächsablauf ("Happy Path")

1. **Begrüßung**
   - User: "Hallo"
   - Bot: "Hallo! Ich bin dein Energieberater..."

2. **Tarifanzeige**
   - User: "Zeig mir Tarife"
   - Bot: Zeigt Liste der verfügbaren Tarife (aus SAP)

3. **Verbrauchsangabe**
   - User: "Ich verbrauche 3500 kWh"
   - Bot: "Verstanden, 3500 kWh. Für welchen Tarif?"

4. **Produktwahl**
   - User: "Green Energy"
   - Bot: "Der Tarif kostet ca. X€ im Jahr. Möchtest du ein Angebot?"

5. **Angebot**
   - User: "Ja, bitte"
   - Bot: "Ab wann soll der Strom fließen?"
   - User: "01.01.2026"
   - Bot: "Angebot wurde erstellt! Deine Angebotsnummer ist XXX."

## 🏗️ Architektur: "Hub & Spoke"

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   FastAPI   │────▶│     SAP     │
└─────────────┘     │   Backend   │     │  S/4HANA    │
┌─────────────┐     │             │     └─────────────┘
│ Web Portal  │────▶│  (main.py)  │
└─────────────┘     │             │     ┌─────────────┐
┌─────────────┐     │             │────▶│   Gemini    │
│   E-Mail    │────▶│             │     │  (Google)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🛠️ SAP Schnittstellen

### Schnittstelle 1: Produktliste
- **URL**: `/http/v1/s4/upil/product/information`
- **Methode**: GET
- **Filter**: `vertriebskanal == 'Chatbot'`

### Schnittstelle 2: Preissimulation
- **URL**: `/http/v1/s4/upil/product/simulation`
- **Methode**: GET (mit JSON Body!)
- **Parameter**: `ConsumptionR1`, `ProductID`, `ConsumptionR2`

### Schnittstelle 3: Angebotserstellung
- **URL**: `/http/v1/servicecloud/create/offer`
- **Methode**: POST
- **Header**: `Gruppe`, `Produkt`
- **Body**: `STARTDATE` (Format: YYYY-MM-DD)

## 📊 State Machine

Der Chatbot verwendet folgende Zustände:

- `START`: Begrüßung
- `SHOWING_PRODUCTS`: Tarife anzeigen
- `WAITING_FOR_CONSUMPTION`: Auf Verbrauchsangabe warten
- `WAITING_FOR_PRODUCT_CHOICE`: Auf Produktauswahl warten
- `SIMULATION_DONE`: Simulation abgeschlossen
- `WAITING_FOR_DATE`: Auf Startdatum warten

## 🤖 LLM Integration

Der `llm_service.py` enthält:
- **System Prompt** für die INTENSE AG Tonalität
- **Entity Extraction** (Regex-Fallback für Zahlen und Datumsangaben)

## 📝 Team & Kontakt

- **Frank Eckert** - Senior Manager / Product-Owner
- **Kemal Musli** - Consultant / Systemintegration
- **Isabelle Wessiepe** - Consultant / Tarifierung

---

**© INTENSE AG | Semester-Projekt 2025**
