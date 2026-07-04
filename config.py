import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# توکن بات تلگرام
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")

# تنظیمات بازی
GAME_CONFIG = {
    "initial_balance": 200,
    "daily_reward": 50,
    "daily_bonus": 100,
    "max_daily_bonus": 500,
}

# تنظیمات سطح‌بندی
LEVEL_CONFIG = {
    "level_1": {"min_balance": 0, "name": "شروع‌کننده", "emoji": "🌟"},
    "level_2": {"min_balance": 500, "name": "مبتدی", "emoji": "⭐"},
    "level_3": {"min_balance": 2000, "name": "درمیانی", "emoji": "💫"},
    "level_4": {"min_balance": 5000, "name": "حرفه‌ای", "emoji": "🔥"},
    "level_5": {"min_balance": 10000, "name": "افسانه‌ای", "emoji": "👑"},
}

# تنظیمات ربات
BOT_CONFIG = {
    "admin_id": None,  # یوزر آی‌دی ادمین برای دریافت گزارش
    "max_players_per_game": 4,
    "game_timeout": 300,  # ۵ دقیقه
}

# تنظیمات پایگاه داده
DB_CONFIG = {
    "db_path": "bot.db",
    "backup_interval": 3600,  # هر ۱ ساعت
}
