
import logging
import httpx
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import settings
from .logger import setup_logging

# Configure Logging
setup_logging()
logger = logging.getLogger(__name__)

BACKEND_URL = "http://127.0.0.1:8000/api/chat"

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    error = context.error
    
    # Handle Network Errors gracefully (don't spam stack trace)
    if isinstance(error, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout)):
        logger.warning(f"⚠️ Telegram Network Error: {error}")
        if isinstance(update, Update) and update.effective_message:
             try:
                 await update.effective_message.reply_text("⚠️ Verbindungsproblem. Bitte versuche es gleich noch einmal.")
             except:
                 pass
        return

    # Check for NetworkError wrapper from telegram
    if hasattr(error, 'message') and "httpx.ConnectError" in str(error):
         logger.warning(f"⚠️ Telegram Connection Failed: {error}")
         return

    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ Ein unerwarteter Fehler ist aufgetreten. Bitte versuche es später noch einmal.")
        except:
            pass


def create_keyboard(ui_data: dict) -> InlineKeyboardMarkup | None:
    """
    Helper to create Telegram InlineKeyboard from backend UI data.
    """
    if not ui_data:
        return None

    ui_type = ui_data.get("type")
    keyboard = []

    if ui_type == "product_selection":
        products = ui_data.get("products", [])
        for p in products:
            p_name = p.get("name", "Produkt")
            p_id = p.get("id")
            # Format price to 2 decimal places
            try:
                price_val = float(p.get('workingPrice', 0))
                price_str = f"{price_val:.2f}".replace('.', ',')
            except:
                price_str = str(p.get('workingPrice'))
                
            # Truncate callback data to fit 64 bytes limit if needed, but ID should be short
            keyboard.append([InlineKeyboardButton(f"⚡ {p_name} ({price_str} ct/kWh)", callback_data=f"prod:{p_id}")])
    
    elif ui_type == "consumption_input":
        keyboard = [
            [InlineKeyboardButton("1500 kWh", callback_data="cons:1500"), InlineKeyboardButton("2500 kWh", callback_data="cons:2500")],
            [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")]
        ]
        
    elif ui_type == "date_input":
        keyboard = [
            [InlineKeyboardButton("Morgen", callback_data="date:tomorrow"), InlineKeyboardButton("01.01.2026", callback_data="date:01.01.2026")],
            [InlineKeyboardButton("01.02.2026", callback_data="date:01.02.2026")]
        ]
        
    elif ui_type == "simulation_result":
        keyboard = [
            [InlineKeyboardButton("✅ Angebot anfordern", callback_data="cmd:angebot")],
            [InlineKeyboardButton("🔄 Verbrauch ändern", callback_data="cmd:change_consumption")]
        ]
    
    elif ui_type == "duration_selection":
        keyboard = [
            [InlineKeyboardButton("12 Monate", callback_data="dur:12"), InlineKeyboardButton("24 Monate", callback_data="dur:24")],
            [InlineKeyboardButton("Egal", callback_data="dur:egal")]
        ]

    elif ui_type == "tariff_type_selection":
        keyboard = [
            [InlineKeyboardButton("Einzeltarif", callback_data="tar:single"), InlineKeyboardButton("Doppeltarif", callback_data="tar:double")],
            [InlineKeyboardButton("Egal", callback_data="tar:egal")]
        ]

    elif ui_type == "offer_success":
        keyboard = [[InlineKeyboardButton("Neuer Start", callback_data="cmd:restart")]]

    if keyboard:
        return InlineKeyboardMarkup(keyboard)
    return None


async def send_backend_request(user_id: str, message: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Sends a message to the backend and handles the response.
    """
    # Send "Typing..." action
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
    
    headers = {"X-API-Key": settings.API_KEY}
    
    payload = {
        "user_id": user_id,
        "message": message,
        "channel": "telegram"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BACKEND_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
        reply_text = data.get("reply", "Keine Antwort vom Server.")
        ui_data = data.get("ui_data", {})
        
        reply_markup = create_keyboard(ui_data)
        
        await context.bot.send_message(
            chat_id=chat_id, 
            text=reply_text, 
            parse_mode=constants.ParseMode.MARKDOWN, 
            reply_markup=reply_markup
        )
        
    except httpx.RequestError as e:
        logger.error(f"Backend Connection Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Fehler bei der Verbindung zum Backend.", parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error processing backend response: {e}")
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Ein unerwarteter Fehler ist aufgetreten.", parse_mode=constants.ParseMode.MARKDOWN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Reset session silently
    try:
        async with httpx.AsyncClient() as client:
            await client.post(BACKEND_URL, json={"user_id": user_id, "message": "reset", "channel": "telegram"}, headers={"X-API-Key": settings.API_KEY}, timeout=5.0)
    except:
        pass
        
    await update.message.reply_text(
        '👋 **Hallo!** Ich bin dein Vertriebs-Bot.\n\nSchreib mir einfach "Hallo" oder "Tarife", um zu starten.',
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    await send_backend_request(user_id, text, context, update.effective_chat.id)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Acknowledge
    
    data = query.data
    user_id = str(update.effective_user.id)
    message_to_send = ""
    
    # Parse callback data
    if data.startswith("prod:"):
        product_id = data.split(":", 1)[1]
        message_to_send = f"SELECT_PRODUCT:{product_id}"
    
    elif data.startswith("cons:"):
        message_to_send = data.split(":", 1)[1]
        
    elif data.startswith("date:"):
        date_val = data.split(":", 1)[1]
        message_to_send = "manual" if date_val == "manual" else date_val
            
    elif data.startswith("cmd:"):
        cmd = data.split(":", 1)[1]
        cmd_map = {
            "angebot": "Ja, Angebot bitte",
            "change_consumption": "Verbrauch ändern",
            "restart": "Start"
        }
        message_to_send = cmd_map.get(cmd, "")
    
    elif data.startswith("dur:"):
        message_to_send = data.split(":", 1)[1]
        
    elif data.startswith("tar:"):
        message_to_send = data.split(":", 1)[1]
            
    if message_to_send:
        # Remove buttons from the old message to prevent double-clicking
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass # Message might be too old or already edited
            
        await send_backend_request(user_id, message_to_send, context, update.effective_chat.id)

if __name__ == '__main__':
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token":
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)
        
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    print("Telegram Bot started...")
    try:
        application.run_polling()
    except Exception as e:
        if "Conflict" in str(e):
            logger.error("❌ Telegram Conflict: Another instance is running. Shutting down.")
            print("❌ Telegram Conflict: Another instance is running. Shutting down.")
        else:
            logger.error(f"❌ Telegram Bot Error: {e}")
