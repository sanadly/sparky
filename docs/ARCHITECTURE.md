# CBI Architecture Documentation

> [!NOTE]
> For detailed documentation on the Backend, API, and Channel Integration, please refer to the [Documentation Index](README.md).


## 1. System Overview

The **CBI (Chat Based Interface)** application, also known as **"Sparky"**, is an intelligent energy consultant chatbot designed to help customers find the best electricity tariffs. It uses a hybrid approach combining a **Deterministic State Machine** for process control (e.g., gathering consumption data) and a **Generative AI (Google Gemini)** for natural language understanding and conversational flexibility.

### Technology Stack

*   **Backend:** Python 3.11+, FastAPI
*   **Frontend:** React 18, Vite, Tailwind CSS
*   **AI/LLM:** Google Gemini Pro (via `google-generativeai`)
*   **Integration:** SAP IS-U (via REST API)
*   **Database:** In-memory Session Store (for this demo version)

---

## 2. Backend Architecture

The backend is built with **FastAPI** and serves as the central orchestrator. It has been refactored into a modular architecture to separate concerns.

### Directory Structure
*   `backend/`: Root package for the backend application.
*   `backend/services/`: Contains business logic and external integrations.

### Core Components

#### 2.1 Entry Point (`backend/main.py`)
*   **FastAPI App:** Initializes the application, mounts static files, and defines API routes.
*   **Orchestration:** Imports services and managers to handle requests.

#### 2.2 State Management (`backend/session_manager.py`)
*   **SessionManager:** Handles user sessions in memory.
*   **State Definitions:** Defines constants for the state machine (e.g., `STATE_WAITING_FOR_CONSUMPTION`).

#### 2.3 Data Models (`backend/schemas.py`)
*   **Pydantic Models:** Defines the structure for API requests and responses (e.g., `UserMessage`, `PitchRequest`).

#### 2.4 Chat Service (`backend/services/chat_service.py`)
*   **Core Logic:** Implements the state machine and business rules.
*   **Flow Control:** Manages the conversation flow from `START` to `OFFER_CREATED`.

#### 2.5 External Services
*   **SAP Integration (`backend/services/sap_client.py`):** Handles authentication, product fetching, simulation, and offer creation with SAP IS-U.
*   **LLM Service (`backend/services/llm_service.py`):** Wraps Google Gemini for entity extraction and natural language generation.

#### 2.6 Telegram Bot (`backend/telegram_bot.py`)
*   **Interface:** Polls Telegram updates and forwards them to the FastAPI backend.

---

## 3. Frontend Architecture

The frontend is a modern **Single Page Application (SPA)** built with React and Vite.

### Core Components

#### 3.1 Main Application (`web-portal/App.tsx`)
*   **Chat Loop:** Manages the list of messages and renders them.
*   **Widget Orchestration:** Decides which interactive widget to show based on `ui_data`.

#### 3.2 Services (`web-portal/services/geminiService.ts`)
*   **API Bridge:** Handles HTTP communication with the backend `/api/chat` endpoint.

---

## 4. Data Flow & Integrations

### Typical User Flow: "I want a tariff"

1.  **User Input:** User types "I want to see tariffs" in the frontend.
2.  **Frontend:** Sends POST request to `/api/chat`.
3.  **Backend (`backend/main.py`):**
    *   Delegates to `ChatService`.
    *   `ChatService` calls `sap_client.get_products()`.
    *   Updates session state via `SessionManager`.
    *   Returns text reply and `ui_data`.
4.  **Frontend:** Renders `ProductCarousel`.

### Configuration
*   **Environment Variables:** Managed via `.env` file (loaded by `backend/config.py`).

