# Backend Architecture & Logic

This document provides a deep dive into the backend of the CBI application.

## 🏗 Directory Structure

The backend is organized as a modular Python package:

```
backend/
├── main.py                 # Entry point (FastAPI app)
├── config.py               # Configuration & Environment variables
├── schemas.py              # Pydantic models for API
├── session_manager.py      # In-memory session & state management
├── telegram_bot.py         # Telegram Channel Adapter
└── services/
    ├── chat_service.py     # CORE LOGIC: State Machine & Orchestration
    ├── llm_service.py      # Google Gemini Integration
    └── sap_client.py       # SAP IS-U Integration
```

## 🧠 Core Components

### 1. ChatService (`services/chat_service.py`)
This is the **brain** of the application. It orchestrates the conversation flow.

*   **Responsibility:** Receives user input, decides the next step (State Machine), interacts with SAP/LLM, and returns a response.
*   **Key Method:** `handle_message(user_id, text)`
    *   Retrieves user session.
    *   Checks for global intents (e.g., "reset").
    *   Dispatches to specific handlers based on current `state` (e.g., `_handle_consumption`, `_handle_product_choice`).

### 2. SessionManager (`session_manager.py`)
Manages user state in memory. In a production environment, this should be replaced by Redis or a Database.

*   **Session Structure:**
    ```python
    {
        "state": "STATE_NAME",  # Current position in the flow
        "data": {               # Context data
            "consumption": 3500,
            "product_id": "123",
            "products": [...]   # Cached product list
        }
    }
    ```

### 3. LLMService (`services/llm_service.py`)
Wraps the Google Gemini API.

*   **`extract_entities(text)`**: Extracts structured data (consumption, dates, product names) from natural language.
*   **`generate_answer(text, context)`**: Generates conversational responses when no hard-coded logic applies.

### 4. SAPClient (`services/sap_client.py`)
Handles all communication with the SAP IS-U backend.

*   **`get_products()`**: Fetches available tariffs.
*   **`simulate_price()`**: Calculates costs based on consumption.
*   **`create_offer()`**: Creates a formal contract offer in SAP.

---

## 🔄 The State Machine

The conversation follows a deterministic flow, augmented by AI for flexibility.

| State | Description | Next Possible States |
| :--- | :--- | :--- |
| `STATE_START` | Initial state. Greets user. | `WAITING_FOR_CONSUMPTION` |
| `WAITING_FOR_CONSUMPTION` | Asks for kWh usage. | `WAITING_FOR_PRODUCT_CHOICE` or `SIMULATION_DONE` |
| `WAITING_FOR_PRODUCT_CHOICE` | Lists products, waits for selection. | `SIMULATION_DONE` |
| `SIMULATION_DONE` | Shows price. Asks for offer. | `WAITING_FOR_DATE` |
| `WAITING_FOR_DATE` | Asks for contract start date. | `OFFER_CREATED` |
| `OFFER_CREATED` | Final state. Shows Offer ID. | `STATE_START` (on reset) |

---

## 🌊 Data Flow

1.  **Request:** Client (Frontend/Bot) sends `POST /api/chat` with `user_id` and `message`.
2.  **Routing:** `main.py` receives request and calls `chat_service.handle_message()`.
3.  **Processing:** `ChatService` checks `SessionManager` for current state.
4.  **Logic:**
    *   If input matches expected data (e.g., "3500 kWh"), it updates state and calls `SAPClient` if needed.
    *   If input is generic question, it calls `LLMService`.
5.  **Response:** Returns a JSON object with:
    *   `reply`: Text to display.
    *   `ui_data`: **Abstract UI** definition (see [Channels Guide](CHANNELS.md)).
    *   `state`: New state.
