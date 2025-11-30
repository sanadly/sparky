import logging
import httpx
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import settings
from .logger import setup_logging
from .telegram_ui import TelegramUI

# Configure Logging
setup_logging()
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000/api/chat"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reset session on backend
    user_id = str(update.effective_user.id)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(BACKEND_URL, json={"user_id": user_id, "message": "reset", "channel": "telegram"})
    except Exception as e:
        logger.error(f"Failed to reset session: {e}")
        
    await update.message.reply_text(
        '👋 **Hallo!** Ich bin dein Vertriebs-Bot.\n\nIch helfe dir, den perfekten Stromtarif zu finden. ⚡\n\nSchreib mir einfach "Hallo" oder "Tarife", um zu starten.',
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(BACKEND_URL, json=payload)
            response.raise_for_status()
            data = response.json()
        
        await _process_backend_response(update, context, data)
        
    except httpx.RequestError as e:
        logger.error(f"Backend Connection Error: {e}")
        await update.message.reply_text(f"⚠️ Fehler bei der Verbindung zum Server. Bitte versuche es später noch einmal.", parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        await update.message.reply_text(f"⚠️ Ein unerwarteter Fehler ist aufgetreten.", parse_mode=constants.ParseMode.MARKDOWN)

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
        message_to_send = f"SELECT_PRODUCT:{product_id}"
    
    elif data.startswith("cons:"):
        consumption = data.split(":", 1)[1]
        message_to_send = str(consumption)
        
    elif data.startswith("date:"):
        date_val = data.split(":", 1)[1]
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
        elif cmd == "show_products":
            message_to_send = "Tarife anzeigen"
        elif cmd == "start_simulation":
            message_to_send = "Simulation starten"
            
    elif data.startswith("msg:"):
        message_to_send = data.split(":", 1)[1]
            
    if message_to_send:
        # Send "Typing..." action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
        
        payload = {
            "user_id": user_id,
            "message": message_to_send,
            "channel": "telegram"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(BACKEND_URL, json=payload)
                response.raise_for_status()
                data = response.json()
            
            # Remove buttons from old message to prevent double-clicking
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass # Message might be too old or already modified

            await _process_backend_response(update, context, data)
            
        except Exception as e:
            logger.error(f"Backend Error in Callback: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Fehler beim Verarbeiten der Auswahl.")

async def _process_backend_response(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    reply_text = data.get("reply", "Keine Antwort vom Server.")
    ui_data = data.get("ui_data", {})
    quick_replies = data.get("quick_replies", [])
    
    reply_markup = None
    
    if ui_data:
        ui_type = ui_data.get("type")
        
        if ui_type == "product_selection":
            products = ui_data.get("products", [])
            reply_markup = TelegramUI.create_product_selection_keyboard(products)
        
        elif ui_type == "consumption_input":
            reply_text += "\n\n💡 *Tipp:* Du kannst auch einfach eine Zahl eintippen (z.B. 3200)."
            reply_markup = TelegramUI.create_consumption_input_keyboard()
            
        elif ui_type == "date_input":
            reply_text += "\n\n📅 *Wann soll der Vertrag starten?*"
            reply_markup = TelegramUI.create_date_input_keyboard()
            
        elif ui_type == "simulation_result":
            reply_markup = TelegramUI.create_simulation_result_keyboard()
        
        elif ui_type == "offer_success":
            offer_id = ui_data.get("offer_id", "Unbekannt")
            reply_text += f"\n\n🆔 Offer ID: `{offer_id}`"
            reply_markup = TelegramUI.create_offer_success_keyboard()

    elif quick_replies:
        reply_markup = TelegramUI.create_quick_replies_keyboard(quick_replies)

    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=reply_text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=reply_markup)

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
