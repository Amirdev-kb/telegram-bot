from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    kb = [
        [InlineKeyboardButton("🎮 مینی‌اپ", callback_data="play_")],
        [InlineKeyboardButton("💰 موجودی", callback_data="balance_cb")],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard_cb")],
        [InlineKeyboardButton("🎁 جایزه روزانه", callback_data="daily_cb")],
    ]
    return InlineKeyboardMarkup(kb)

def play_menu():
    kb = [
        [InlineKeyboardButton("▶️ شروع بازی", callback_data="play_")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def chests_markup():
    kb = [
        [
            InlineKeyboardButton("📦 صندوق ۱", callback_data="chest_1"),
            InlineKeyboardButton("📦 صندوق ۲", callback_data="chest_2"),
            InlineKeyboardButton("📦 صندوق ۳", callback_data="chest_3"),
        ]
    ]
    return InlineKeyboardMarkup(kb)

def after_play_markup():
    kb = [
        [InlineKeyboardButton("🔁 دوباره بازی کن", callback_data="play_again")],
        [InlineKeyboardButton("🔙 منو", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(kb)
