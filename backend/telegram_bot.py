
import logging
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import settings
from .logger import setup_logging

# Configure Logging
setup_logging()
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000/api/chat"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reset session on backend
    user_id = str(update.effective_user.id)
    try:
        requests.post(BACKEND_URL, json={"user_id": user_id, "message": "reset", "channel": "telegram"})
    except:
        pass
        
    await update.message.reply_text(
        '👋 **Hallo!** Ich bin dein Vertriebs-Bot.\n\nSchreib mir einfach "Hallo" oder "Tarife", um zu starten.',
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Send "Typing..." action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    # Send to Backend
    payload = {
        "user_id": user_id,
        "message": text,
        "channel": "telegram"
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        
        reply_text = data.get("reply", "Keine Antwort vom Server.")
        ui_data = data.get("ui_data", {})
        quick_replies = data.get("quick_replies", []) # Support for quick replies (e.g. Reset Confirm)
        
        # Prepare Keyboard based on ui_data OR quick_replies
        reply_markup = None
        
        if ui_data:
            ui_type = ui_data.get("type")
            
            if ui_type == "product_selection":
                products = ui_data.get("products", [])
                keyboard = []
                for p in products:
                    p_name = p.get("name", "Produkt")
                    p_id = p.get("id")
                    keyboard.append([InlineKeyboardButton(f"⚡ {p_name} ({p.get('workingPrice')} ct/kWh)", callback_data=f"prod:{p_id}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            elif ui_type == "consumption_input":
                keyboard = [
                    [InlineKeyboardButton("1500 kWh", callback_data="cons:1500"), InlineKeyboardButton("2500 kWh", callback_data="cons:2500")],
                    [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            elif ui_type == "date_input":
                keyboard = [
                    [InlineKeyboardButton("Morgen", callback_data="date:tomorrow"), InlineKeyboardButton("01.01.2026", callback_data="date:01.01.2026")],
                    [InlineKeyboardButton("01.02.2026", callback_data="date:01.02.2026")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            elif ui_type == "simulation_result":
                keyboard = [
                    [InlineKeyboardButton("✅ Angebot anfordern", callback_data="cmd:angebot")],
                    [InlineKeyboardButton("🔄 Verbrauch ändern", callback_data="cmd:change_consumption")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            elif ui_type == "offer_success":
                offer_id = ui_data.get("offer_id", "Unbekannt")
                # Enhance reply text with monospaced ID for easy copying
                reply_text += f"\n\n🆔 Offer ID: `{offer_id}`"
                
                keyboard = [[InlineKeyboardButton("🔄 Neuer Start", callback_data="cmd:restart")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

        # Fallback: Check for Quick Replies (e.g. Reset Confirmation)
        elif quick_replies:
            keyboard = []
            row = []
            for qr in quick_replies:
                # Map text to callback data
                cb_data = "cmd:unknown"
                if "ja" in qr.lower() or "neustart" in qr.lower():
                    cb_data = "cmd:reset_confirm"
                elif "nein" in qr.lower() or "weiter" in qr.lower():
                    cb_data = "cmd:reset_cancel"
                else:
                    # Generic fallback for other quick replies
                    cb_data = f"msg:{qr[:20]}" 
                
                row.append(InlineKeyboardButton(qr, callback_data=cb_data))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(reply_text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Backend Error: {e}")
        await update.message.reply_text(f"⚠️ Fehler bei der Verbindung zum Backend.", parse_mode=constants.ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles button clicks.
    """
    query = update.callback_query
    await query.answer() # Acknowledge the click
    
    data = query.data
    user_id = str(update.effective_user.id)
    message_to_send = ""
    
    if data.startswith("prod:"):
        product_id = data.split(":", 1)[1]
        # Send a special command that the backend understands directly
        message_to_send = f"SELECT_PRODUCT:{product_id}"
    
    elif data.startswith("cons:"):
        consumption = data.split(":", 1)[1]
        message_to_send = str(consumption)
        
    elif data.startswith("date:"):
        date_val = data.split(":", 1)[1]
        if date_val == "tomorrow":
            message_to_send = "Morgen" 
        else:
            message_to_send = date_val
            
    elif data.startswith("cmd:"):
        cmd = data.split(":", 1)[1]
        if cmd == "angebot":
            message_to_send = "Ja, Angebot bitte"
        elif cmd == "change_consumption":
            message_to_send = "Verbrauch ändern"
        elif cmd == "restart":
            message_to_send = "Start"
        elif cmd == "reset_confirm":
            message_to_send = "Ja, Neustart"
        elif cmd == "reset_cancel":
            message_to_send = "Nein, weiter"
            
    elif data.startswith("msg:"):
        message_to_send = data.split(":", 1)[1]
            
    if message_to_send:
        # Send "Typing..." action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
        
        # Send simulated user message to backend
        payload = {
            "user_id": user_id,
            "message": message_to_send,
            "channel": "telegram"
        }
        
        try:
            response = requests.post(BACKEND_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            reply_text = data.get("reply", "")
            ui_data = data.get("ui_data", {})
            quick_replies = data.get("quick_replies", [])
            
            # Prepare Keyboard based on ui_data
            reply_markup = None
            
            if ui_data:
                ui_type = ui_data.get("type")
                
                if ui_type == "product_selection":
                    products = ui_data.get("products", [])
                    keyboard = []
                    for p in products:
                        p_name = p.get("name", "Produkt")
                        p_id = p.get("id")
                        keyboard.append([InlineKeyboardButton(f"⚡ {p_name} ({p.get('workingPrice')} ct/kWh)", callback_data=f"prod:{p_id}")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                
                elif ui_type == "consumption_input":
                    keyboard = [
                        [InlineKeyboardButton("1500 kWh", callback_data="cons:1500"), InlineKeyboardButton("2500 kWh", callback_data="cons:2500")],
                        [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                elif ui_type == "date_input":
                    keyboard = [
                        [InlineKeyboardButton("Morgen", callback_data="date:tomorrow"), InlineKeyboardButton("01.01.2026", callback_data="date:01.01.2026")],
                        [InlineKeyboardButton("01.02.2026", callback_data="date:01.02.2026")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                elif ui_type == "simulation_result":
                    keyboard = [
                        [InlineKeyboardButton("✅ Angebot anfordern", callback_data="cmd:angebot")],
                        [InlineKeyboardButton("🔄 Verbrauch ändern", callback_data="cmd:change_consumption")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                
                elif ui_type == "offer_success":
                    offer_id = ui_data.get("offer_id", "Unbekannt")
                    reply_text += f"\n\n🆔 Offer ID: `{offer_id}`"
                    keyboard = [[InlineKeyboardButton("🔄 Neuer Start", callback_data="cmd:restart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

            # Fallback: Check for Quick Replies (e.g. Reset Confirmation)
            elif quick_replies:
                keyboard = []
                row = []
                for qr in quick_replies:
                    cb_data = "cmd:unknown"
                    if "ja" in qr.lower() or "neustart" in qr.lower():
                        cb_data = "cmd:reset_confirm"
                    elif "nein" in qr.lower() or "weiter" in qr.lower():
                        cb_data = "cmd:reset_cancel"
                    else:
                        cb_data = f"msg:{qr[:20]}"
                    
                    row.append(InlineKeyboardButton(qr, callback_data=cb_data))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
                reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_reply_markup(reply_markup=None) # Remove buttons from old message
            await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Backend Error in callback: {e}")
            await query.message.reply_text(f"⚠️ Fehler bei der Verbindung zum Backend.", parse_mode=constants.ParseMode.MARKDOWN)
            
            # Handle UI data for callback responses too (Recursion logic duplicated for simplicity)
            reply_markup = None
            if ui_data:
                ui_type = ui_data.get("type")
                if ui_type == "product_selection":
                    products = ui_data.get("products", [])
                    keyboard = []
                    for p in products:
                        p_name = p.get("name", "Produkt")
                        keyboard.append([InlineKeyboardButton(f"⚡ {p_name} ({p.get('workingPrice')} ct/kWh)", callback_data=f"prod:{p_name[:40]}")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                elif ui_type == "consumption_input":
                    keyboard = [
                        [InlineKeyboardButton("1500 kWh", callback_data="cons:1500"), InlineKeyboardButton("2500 kWh", callback_data="cons:2500")],
                        [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                elif ui_type == "date_input":
                    keyboard = [
                        [InlineKeyboardButton("Morgen", callback_data="date:tomorrow"), InlineKeyboardButton("01.01.2026", callback_data="date:01.01.2026")],
                        [InlineKeyboardButton("01.02.2026", callback_data="date:01.02.2026")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                elif ui_type == "simulation_result":
                    keyboard = [
                        [InlineKeyboardButton("✅ Angebot anfordern", callback_data="cmd:angebot")],
                        [InlineKeyboardButton("🔄 Verbrauch ändern", callback_data="cmd:change_consumption")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                elif ui_type == "offer_success":
                    keyboard = [[InlineKeyboardButton("Neuer Start", callback_data="cmd:restart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_reply_markup(reply_markup=None) # Remove buttons from old message
            await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Backend Error in Callback: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Fehler beim Verarbeiten der Auswahl.")

if __name__ == '__main__':
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token":
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)
        
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    callback_handler = CallbackQueryHandler(handle_callback)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    application.add_handler(callback_handler)
    
    print("Telegram Bot started...")
    application.run_polling()
