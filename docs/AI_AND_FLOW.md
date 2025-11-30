# Application Flow and AI Usage

## Overview
This application is a hybrid chatbot for energy tariff consultation. It combines a deterministic state machine for critical business logic (product selection, simulation, offer creation) with an AI layer (Google Gemini) for natural language understanding and conversational fluency.

## User Flow

The user journey follows a linear path, managed by the `SessionManager` and `ChatService`.

1.  **Start (`STATE_START`)**
    *   **User Action**: Sends "Hallo", "Start", or asks a question.
    *   **System Response**: Welcomes the user and offers to show tariffs or start a simulation.
    *   **AI Role**: Handles chit-chat and general questions.

2.  **Product Selection (`STATE_WAITING_FOR_CONSUMPTION` / `STATE_WAITING_FOR_PRODUCT_CHOICE`)**
    *   **User Action**: Selects a product (via button or text) or enters consumption.
    *   **System Response**:
        *   If product selected: Asks for consumption.
        *   If consumption given: Asks for product (if not yet chosen).
    *   **AI Role**: Extracts product names and consumption values from natural language (e.g., "I want the Green one and use 3500 kWh").

3.  **Simulation (`STATE_SIMULATION_DONE`)**
    *   **User Action**: Confirms the simulation result or asks to change parameters.
    *   **System Logic**:
        *   Splits consumption (70/30) for Double Tariff products.
        *   Calls SAP `simulate_price` API.
    *   **System Response**: Shows the calculated price and asks if the user wants an offer.

4.  **Offer Creation (`STATE_WAITING_FOR_DATE`)**
    *   **User Action**: Provides a start date.
    *   **System Logic**:
        *   Validates date.
        *   Calls SAP `create_offer` API with Product, Consumption, and Date.
    *   **System Response**: Returns a generated Offer ID.

## AI Integration (Google Gemini)

The `LLMService` uses Google Gemini to enhance the user experience without losing control of the business process.

### 1. Intent & Entity Extraction
Instead of relying solely on regex, the app sends user input to Gemini to extract structured data:
*   **Intent**: `selection`, `recommendation`, `question`, `correction`, `confirmation`.
*   **Entities**:
    *   `consumption` (kWh)
    *   `date` (YYYY-MM-DD)
    *   `product_name`

**Example**:
> User: "Ich verbrauche so 2500 und hätte gerne den Ökostrom ab nächstem Monat."
> AI Extracts: `{"consumption": 2500, "product_name": "Green Energy", "date": "2023-12-01"}`

### 2. Fallback & Chit-Chat
If the user asks a question not related to the immediate flow (e.g., "Was ist der Unterschied zwischen HT und NT?"), the AI generates a helpful, context-aware response using a system prompt that defines its persona as a "friendly energy consultant".

### 3. Hybrid Approach
*   **Priority**: The State Machine always checks for specific state-based inputs first.
*   **Support**: If the State Machine cannot handle the input (e.g., complex sentence), it delegates to the AI for extraction or answer generation.
*   **Safety**: Critical actions (SAP calls) are hard-coded and only triggered when validated data is available, preventing the AI from "hallucinating" API calls or prices.
