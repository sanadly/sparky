# API Reference

## Base URL
`http://localhost:8000`

---

## 1. Chat Endpoint
**POST** `/api/chat`

Main endpoint for all conversational interactions.

### Request Body
```json
{
  "user_id": "string",    // Unique identifier for the user (e.g., Session ID, Email, Telegram ID)
  "message": "string",    // The user's input text
  "channel": "string"     // Source channel (e.g., "web", "telegram", "email")
}
```

### Response Body
```json
{
  "reply": "string",      // The text response to display to the user
  "state": "string",      // The current state of the conversation (e.g., "STATE_WAITING_FOR_CONSUMPTION")
  "ui_data": {            // Optional. Abstract UI definition.
    "type": "string",     // e.g., "product_selection", "consumption_input"
    ...                   // Additional fields depend on 'type'
  }
}
```

---

## 2. Pitch Endpoint
**POST** `/api/pitch`

Helper endpoint to generate marketing pitches for products using GenAI.

### Request Body
```json
{
  "product_name": "string",
  "is_green": boolean,
  "consumption": integer
}
```

### Response Body
```json
{
  "pitch": "string"       // A short, persuasive marketing sentence.
}
```
