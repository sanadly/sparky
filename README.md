# INTENSE Energieberater - Multi-Channel Chatbot

Ein intelligenter Chatbot für die Energietarifberatung, entwickelt als Semester-Projekt für INTENSE AG.

> **📘 Documentation**
>
> Detailed technical documentation is available in the [docs/](docs/) directory.
> - [Architecture](docs/ARCHITECTURE.md)
> - [Deployment](docs/DEPLOYMENT.md)
> - [API Reference](docs/API_REFERENCE.md)

## 🎯 Projektübersicht

Dieser Chatbot ermöglicht Kunden die Beratung zu Energietarifen über mehrere Kanäle:
- **Web Portal** (React/Vite Interface)
- **Telegram Bot** (@SparkyBerater_bot)
- **E-Mail** (Automatische Angebotserstellung)

### Hauptfunktionen
1. **Intelligente Tarifberatung**: Zeigt verfügbare Tarife basierend auf SAP-Produktdaten.
2. **Preissimulation**: Berechnet Kosten basierend auf Jahresverbrauch (HT/NT Split).
3. **Angebotserstellung**: Erstellt automatisch Angebote im SAP Sales & Service Cloud.
4. **Persistenz**: Speichert Chat-Status über Redis.

## 🚀 Quick Start (Docker)

Die einfachste Art, das Projekt zu starten, ist mit Docker.

**Voraussetzungen:** Docker Desktop installiert.

```bash
# 1. Repository klonen
git clone <repo-url>
cd CBI

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
# Bearbeite .env und füge deine API-Keys hinzu!

# 3. Starten
docker-compose up --build
```

- **Web Portal**: `http://localhost:80`
- **Backend API**: `http://localhost:8000`

## 🏗️ Architektur

Das System folgt einer modernen Microservices-ähnlichen Architektur:

```mermaid
graph TD
    User[User] --> Web[Web Portal (React)]
    User --> Telegram[Telegram Bot]
    
    Web --> API[Backend API (FastAPI)]
    Telegram --> API
    
    subgraph Backend
        API --> ChatService
        ChatService --> ProductService
        ChatService --> SimulationService
        ChatService --> IntentService
        
        SessionManager --> Redis[(Redis)]
    end
    
    ProductService --> SAP[SAP S/4HANA]
    SimulationService --> SAP
    IntentService --> LLM[Google Gemini / DeepSeek]
```

### Services
- **ProductService**: Produktsuche und -filterung.
- **SimulationService**: Preissimulation und Verbrauchsaufteilung.
- **IntentService**: KI-Logik für Absichtserkennung.
- **SessionManager**: Verwaltet User-Sessions in Redis.

## 🛠️ Entwicklung (Lokal)

Falls du ohne Docker entwickeln möchtest:

### Backend
```bash
# Virtual Environment
python -m venv venv
source venv/bin/activate

# Installieren
pip install -r requirements.txt

# Starten (API)
./run.sh

# Starten (Email Worker)
python -m backend.email_worker
```

### Frontend
```bash
cd web-portal
npm install
npm run dev
```

## 📝 Team & Kontakt

- **Frank Eckert** - Senior Manager / Product-Owner
- **Kemal Musli** - Consultant / Systemintegration
- **Isabelle Wessiepe** - Consultant / Tarifierung

---
**© INTENSE AG | Semester-Projekt 2025**
