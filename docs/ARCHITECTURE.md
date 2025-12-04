# Architecture Documentation

## Overview

The system is designed as a modular backend serving multiple frontend channels. It uses FastAPI for the API layer, Redis for state management, and integrates with SAP and LLM providers.

## Core Components

### 1. Backend Services (`backend/services/`)

The monolithic `ChatService` has been refactored into specialized services:

- **`ProductService`**: 
  - Handles fetching products from SAP.
  - Implements fuzzy matching (`find_product_in_text`) to identify products in user messages.
  - Formats product data for the UI.

- **`SimulationService`**:
  - Handles consumption logic (splitting total consumption into HT/NT).
  - Calls SAP simulation endpoint to calculate prices.

- **`IntentService`**:
  - Encapsulates LLM interactions.
  - Extracts entities (consumption, dates, household size) from text.
  - Generates fallback answers.

- **`ChatService`**:
  - Orchestrator that manages the conversation flow.
  - Uses the State Machine pattern to transition between states (`START`, `WAITING_FOR_CONSUMPTION`, etc.).
  - Delegates tasks to the specialized services.

### 2. State Management (`backend/session_manager.py`)

- **Redis**: Used as the primary session store.
- **Persistence**: Sessions expire after 1 hour of inactivity.
- **Structure**:
  ```json
  {
    "state": "WAITING_FOR_CONSUMPTION",
    "data": {
      "product_id": "123",
      "consumption": 3500
    },
    "last_activity": 1715432100.0
  }
  ```

### 3. Frontend (`web-portal/`)

- **React/Vite**: Modern SPA framework.
- **ApiClient**: Centralized API handling in `services/api/client.ts`.
- **TailwindCSS**: Utility-first styling.

## Data Flow

1. **Message Received**: User sends a message via Web or Telegram.
2. **Session Retrieval**: `SessionManager` fetches current state from Redis.
3. **Intent Recognition**: `IntentService` analyzes the message.
4. **Action Execution**: `ChatService` executes logic (e.g., call `ProductService`).
5. **State Update**: New state is saved to Redis.
6. **Response**: Reply is sent back to the user.

## External Integrations

- **SAP S/4HANA**: Product data, Price Simulation, Offer Creation.
- **LLM (Gemini/DeepSeek)**: Natural Language Understanding.
- **SMTP/IMAP**: Email communication.
