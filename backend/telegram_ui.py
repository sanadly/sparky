from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class TelegramUI:
    @staticmethod
    def create_product_selection_keyboard(products):
        keyboard = []
        for p in products:
            p_name = p.get("name", "Produkt")
            p_id = p.get("id")
            is_green = p.get("isGreen", False)
            icon = "🌱" if is_green else "⚡"
            
            try:
                price = float(p.get('workingPrice', 0))
                price_str = f"{price:.2f}".replace('.', ',')
            except:
                price_str = str(p.get('workingPrice'))
                
            # Truncate name if too long to avoid button errors
            display_name = f"{icon} {p_name}"[:30]
            keyboard.append([InlineKeyboardButton(f"{display_name} ({price_str} ct/kWh)", callback_data=f"prod:{p_id}")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_consumption_input_keyboard():
        keyboard = [
            [InlineKeyboardButton("1500 kWh", callback_data="cons:1500"), InlineKeyboardButton("2500 kWh", callback_data="cons:2500")],
            [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_date_input_keyboard():
        # Static dates for now, could be dynamic
        keyboard = [
            [InlineKeyboardButton("01.01.2026", callback_data="date:01.01.2026"), InlineKeyboardButton("01.02.2026", callback_data="date:01.02.2026")],
            [InlineKeyboardButton("01.03.2026", callback_data="date:01.03.2026")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_simulation_result_keyboard():
        keyboard = [
            [InlineKeyboardButton("✅ Angebot anfordern", callback_data="cmd:angebot")],
            [InlineKeyboardButton("🔄 Verbrauch ändern", callback_data="cmd:change_consumption")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_offer_success_keyboard():
        keyboard = [[InlineKeyboardButton("🔄 Neuer Start", callback_data="cmd:restart")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_quick_replies_keyboard(quick_replies):
        keyboard = []
        row = []
        for qr in quick_replies:
            cb_data = "cmd:unknown"
            if "ja" in qr.lower() or "neustart" in qr.lower():
                cb_data = "cmd:reset_confirm"
            elif "nein" in qr.lower() or "weiter" in qr.lower():
                cb_data = "cmd:reset_cancel"
            elif "tarife" in qr.lower():
                cb_data = "cmd:show_products"
            elif "simulation" in qr.lower():
                cb_data = "cmd:start_simulation"
            else:
                cb_data = f"msg:{qr[:20]}"
            
            row.append(InlineKeyboardButton(qr, callback_data=cb_data))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
