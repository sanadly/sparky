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
            [InlineKeyboardButton("3500 kWh", callback_data="cons:3500"), InlineKeyboardButton("5000 kWh", callback_data="cons:5000")],
            [InlineKeyboardButton("✏️ Anderer Wert", callback_data="cons:manual")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_date_input_keyboard():
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        today = datetime.now()
        
        # Helper to get 1st of next month
        def get_next_month_first(date_obj):
            if date_obj.day == 1:
                return date_obj + relativedelta(months=1)
            return (date_obj.replace(day=1) + relativedelta(months=1))

        next_month = get_next_month_first(today)
        in_3_months = next_month + relativedelta(months=3)
        in_1_year = next_month + relativedelta(years=1)
        
        fmt = "%d.%m.%Y"
        
        keyboard = [
            [InlineKeyboardButton(f"Ab {next_month.strftime(fmt)}", callback_data=f"date:{next_month.strftime(fmt)}")],
            [InlineKeyboardButton(f"In 3 Monaten ({in_3_months.strftime(fmt)})", callback_data=f"date:{in_3_months.strftime(fmt)}")],
            [InlineKeyboardButton(f"In 1 Jahr ({in_1_year.strftime(fmt)})", callback_data=f"date:{in_1_year.strftime(fmt)}")],
            [InlineKeyboardButton("✏️ Anderes Datum", callback_data="date:manual")]
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
