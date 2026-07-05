from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def main_menu():
    """منوی اصلی"""
    kb = [
        [InlineKeyboardButton("🎮 بازی‌ها", callback_data="games_menu")],
        [InlineKeyboardButton("💰 موجودی", callback_data="balance_cb")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile_cb")],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard_cb")],
        [InlineKeyboardButton("🎁 جایزه روزانه", callback_data="daily_cb")],
        [InlineKeyboardButton("🏅 دستاوردها", callback_data="achievements_cb")],
    ]
    return InlineKeyboardMarkup(kb)

def games_menu():
    """منوی بازی‌ها"""
    kb = [
        [InlineKeyboardButton("📦 صندوق‌های گنج", callback_data="play_chest")],
        [InlineKeyboardButton("🎲 رول تاس", callback_data="play_dice")],
        [InlineKeyboardButton("✨ شماره خوشبخت", callback_data="play_lucky")],
        [InlineKeyboardButton("🪙 پرتاب سکه", callback_data="play_coin")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def chests_markup():
    """صندوق‌های گنج"""
    kb = [
        [
            InlineKeyboardButton("📦 صندوق ۱", callback_data="chest_1"),
            InlineKeyboardButton("📦 صندوق ۲", callback_data="chest_2"),
            InlineKeyboardButton("📦 صندوق ۳", callback_data="chest_3"),
        ],
        [InlineKeyboardButton("🔙 برگشت", callback_data="games_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def lucky_number_markup():
    """شماره‌های ۱ تا ۱۰"""
    kb = []
    for i in range(1, 11):
        kb.append([InlineKeyboardButton(str(i), callback_data=f"lucky_{i}")])
    kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="games_menu")])
    return InlineKeyboardMarkup(kb)

def coin_flip_markup():
    """انتخاب شیر یا خط"""
    kb = [
        [
            InlineKeyboardButton("🪙 شیر", callback_data="coin_heads"),
            InlineKeyboardButton("🪙 خط", callback_data="coin_tails"),
        ],
        [InlineKeyboardButton("🔙 برگشت", callback_data="games_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def dice_roll_markup():
    """رول تاس"""
    kb = [
        [InlineKeyboardButton("🎲 رول کن!", callback_data="dice_roll_action")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="games_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def after_play_markup():
    """بعد از بازی"""
    kb = [
        [InlineKeyboardButton("🔁 دوباره بازی", callback_data="games_menu")],
        [InlineKeyboardButton("🔙 منو", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def back_to_menu():
    """برگشت به منو"""
    kb = [
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(kb)

def level_emoji(level):
    """ایموجی سطح"""
    levels = {
        1: "🌟",
        2: "⭐",
        3: "💫",
        4: "🔥",
        5: "👑",
    }
    return levels.get(level, "🌟")

def level_name(level):
    """نام سطح"""
    names = {
        1: "شروع‌کننده",
        2: "مبتدی",
        3: "درمیانی",
        4: "حرفه‌ای",
        5: "افسانه‌ای",
    }
    return names.get(level, "نامعلوم")

def format_user_stats(stats):
    """قالب‌بندی آمار کاربر"""
    text = f"""
👤 <b>{stats['name']}</b>

💰 موجودی: {stats['balance']} سکه
🎖️ سطح: {level_emoji(stats['level'])} {level_name(stats['level'])}

📊 آمار:
   🏆 برد: {stats['total_wins']}
   ❌ باخت: {stats['total_losses']}
   🎮 کل بازی: {stats['total_games']}
   📈 درصد برد: {stats['win_rate']}

📅 عضویت: {stats['created_at'][:10]}
"""
    return text

def format_leaderboard(leaderboard):
    """قالب‌بندی جدول امتیازات"""
    text = "🏆 <b>جدول امتیازات</b>\n\n"
    for i, player in enumerate(leaderboard, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        text += f"{medal} {player['name']}\n"
        text += f"   💰 {player['balance']} سکه | {level_emoji(player['level'])} {level_name(player['level'])}\n"
        text += f"   🏆 {player['wins']} برد\n\n"
    return text

def format_achievements(achievements):
    """قالب‌بندی دستاوردها"""
    if not achievements:
        return "هنوز دستاورد باز نکردی! 🎯"
    
    text = "🏅 <b>دستاوردهای شما</b>\n\n"
    for achievement in achievements:
        text += f"✨ <b>{achievement['name']}</b>\n"
        text += f"   {achievement['description']}\n\n"
    return text
