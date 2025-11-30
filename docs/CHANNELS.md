# Channel Integration Guide

One of the key features of CBI is its **Multi-Channel Architecture**. The backend logic is decoupled from the specific frontend implementation (Web, Telegram, Email, etc.).

## 🧩 The "Abstract UI" Concept

Instead of returning HTML or platform-specific JSON (like Telegram buttons), the backend returns **Abstract UI Data** (`ui_data`).

**Example `ui_data`:**
```json
{
  "type": "product_selection",
  "products": [
    {"id": "1", "name": "Eco Power", "price": 30.5},
    {"id": "2", "name": "Basic", "price": 28.0}
  ]
}
```

**Responsibility of the Channel Adapter:**
*   **Web Frontend:** Renders a React Carousel component.
*   **Telegram Bot:** Renders Inline Keyboard Buttons.
*   **Email:** Renders an HTML table or a bulleted list.
*   **Voice/Phone:** Reads out the options ("Press 1 for Eco Power...").

---

## 🛠 How to Add a New Channel (e.g., Email)

Let's say you want to allow users to interact via Email.

### Step 1: Create the Channel Adapter
You need a script or service that listens for incoming emails (e.g., using IMAP or SendGrid Webhooks).

### Step 2: Forward to Backend
When an email arrives, extract the `sender_email` (use as `user_id`) and the `body` (message).

```python
# Pseudo-code for Email Adapter
import requests

def on_email_received(sender, body):
    response = requests.post("http://localhost:8000/api/chat", json={
        "user_id": sender,
        "message": body,
        "channel": "email"
    })
    
    handle_backend_response(sender, response.json())
```

### Step 3: Handle the Response & `ui_data`
You must convert the backend's abstract response into an Email format.

```python
def handle_backend_response(recipient, data):
    text_reply = data.get("reply")
    ui_data = data.get("ui_data")
    
    html_body = f"<p>{text_reply}</p>"
    
    # RENDER ABSTRACT UI FOR EMAIL
    if ui_data:
        if ui_data["type"] == "product_selection":
            html_body += "<ul>"
            for p in ui_data["products"]:
                html_body += f"<li><b>{p['name']}</b>: {p['workingPrice']} ct/kWh</li>"
            html_body += "</ul>"
            html_body += "<p>Reply with the name of the product you want.</p>"
            
        elif ui_data["type"] == "simulation_result":
            res = ui_data["data"]
            html_body += f"<div style='border:1px solid #ccc; padding:10px;'>"
            html_body += f"<h3>Estimated Cost: {res['product']['totalPrice']} EUR</h3>"
            html_body += "</div>"
            
    send_email(to=recipient, subject="Your Energy Consultant", html=html_body)
```

### Step 4: Handle User Replies
When the user replies to the email, the cycle repeats. Since the backend uses `user_id` (email address) to track session state, the context is preserved automatically!

---

## 📋 Supported UI Types

Ensure your new channel handles these `ui_data` types:

1.  **`product_selection`**: List of products.
    *   *Email:* List or Table.
    *   *Voice:* Read out names.
2.  **`consumption_input`**: Request for number.
    *   *Email:* "Please reply with your kWh usage."
3.  **`date_input`**: Request for date.
    *   *Email:* "Please reply with start date (DD.MM.YYYY)."
4.  **`simulation_result`**: Display calculation.
    *   *Email:* Highlighted cost box.
5.  **`offer_success`**: Final confirmation.
    *   *Email:* Formal confirmation text.
