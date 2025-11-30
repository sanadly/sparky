# CBI (Chat Based Interface) Documentation

Welcome to the documentation for the **CBI (Sparky)** project. This documentation is designed to help developers understand the architecture, backend logic, and how to extend the system with new channels.

## 📚 Documentation Index

### 1. [Backend Architecture](BACKEND.md)
Detailed explanation of the backend structure, services, state machine, and data flow.
*   **Key Topics:** `ChatService`, `SessionManager`, `SAPClient`, State Machine Logic.

### 2. [Channel Integration Guide](CHANNELS.md)
**Want to add Email, WhatsApp, or Slack?** Read this guide.
*   Explains the "Abstract UI" pattern.
*   Step-by-step guide to adding new channels.
*   How to handle `ui_data` responses.

### 3. [API Reference](API_REFERENCE.md)
Technical details of the REST API endpoints.
*   `/api/chat`: The main conversational endpoint.
*   `/api/pitch`: Helper endpoint for generating sales pitches.

### 4. [System Architecture](ARCHITECTURE.md)
High-level overview of the entire system (Frontend + Backend + AI).

---

## 🚀 Quick Start

### Prerequisites
*   Python 3.11+
*   Node.js 18+ (for Frontend)
*   SAP IS-U Credentials (configured in `.env`)
*   Google Gemini API Key (configured in `.env`)

### Running the Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The API will be available at `http://localhost:8000`.

### Running the Telegram Bot
```bash
# In a separate terminal
python -m backend.telegram_bot
```
