from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import config
import storage
import game
import ui
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    storage.ensure_db()
    storage.create_or_get_user(user.id, update.effective_chat.id, user.full_name)
    
    welcome_text = """
سلام 👋 به ربات پیشرفته Coin Collector خوش اومدی!

🎮 این ربات شامل:
• بازی‌های متنوع و هیجان‌انگیز
• سیستم سطح‌بندی ۵ سطحی
• جدول امتیازات و رقابت
• دستاوردهای قابل باز کردن
• جایزه روزانه

برای شروع /menu رو بزن! 🚀
"""
    await update.message.reply_text(welcome_text)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی"""
    kb = ui.main_menu()
    await update.message.reply_text("📋 <b>منوی اصلی</b>", reply_markup=kb, parse_mode="HTML")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش موجودی"""
    user = update.effective_user
    u = storage.create_or_get_user(user.id, update.effective_chat.id, user.full_name)
    storage.update_user_level(user.id)
    
    level = storage.get_user_level(user.id)
    text = f"""
💰 <b>موجودی شما</b>

💵 مبلغ: {u['balance']} سکه
🎖️ سطح: {ui.level_emoji(level)} {ui.level_name(level)}

برای بازی‌های بیشتر به منو برو! 🎮
"""
    kb = ui.back_to_menu()
    await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پروفایل"""
    user = update.effective_user
    stats = storage.get_user_stats(user.id)
    
    if stats:
        text = ui.format_user_stats(stats)
        kb = ui.back_to_menu()
        await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await update.message.reply_text("اطلاعات کاربری پیدا نشد.")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جدول امتیازات"""
    top = storage.get_leaderboard(limit=10)
    text = ui.format_leaderboard(top)
    kb = ui.back_to_menu()
    await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جایزه روزانه"""
    user = update.effective_user
    ok, amount, msg = storage.claim_daily(user.id)
    
    if ok:
        text = f"🎁 <b>جایزه روزانه</b>\n\n✅ {msg}\n\n💰 شما {amount} سکه دریافت کردی!"
    else:
        text = f"⏳ <b>جایزه روزانه</b>\n\n❌ {msg}"
    
    kb = ui.back_to_menu()
    await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")

async def achievements_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش دستاوردها"""
    user = update.effective_user
    achievements = storage.get_user_achievements(user.id)
    text = ui.format_achievements(achievements)
    kb = ui.back_to_menu()
    await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های Callback"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    
    # منو اصلی
    if data == "back_menu":
        kb = ui.main_menu()
        await query.edit_message_text("📋 <b>منوی اصلی</b>", reply_markup=kb, parse_mode="HTML")
    
    # منوی بازی‌ها
    elif data == "games_menu":
        kb = ui.games_menu()
        await query.edit_message_text("🎮 <b>انتخاب بازی</b>\n\nکدام بازی رو بازی کنی؟", reply_markup=kb, parse_mode="HTML")
    
    # صندوق‌های گنج
    elif data == "play_chest":
        kb = ui.chests_markup()
        await query.edit_message_text("📦 <b>صندوق‌های گنج</b>\n\nیکی از صندوق‌ها رو انتخاب کن:", reply_markup=kb, parse_mode="HTML")
    
    elif data.startswith("chest_"):
        choice = int(data.split("_")[1])
        result = game.open_chest(user.id, choice)
        storage.add_balance(user.id, result['amount'])
        storage.log_play(user.id, result['amount'], result['outcome'], "chest")
        storage.update_user_level(user.id)
        
        current_balance = storage.get_user_balance(user.id)
        text = f"""
📦 <b>نتیجه صندوق</b>

{result['outcome_text']}

💰 موجودی فعلی: {current_balance} سکه
"""
        kb = ui.after_play_markup()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # رول تاس
    elif data == "play_dice":
        kb = ui.dice_roll_markup()
        await query.edit_message_text("🎲 <b>رول تاس</b>\n\nدکمه رول کن رو بزن:", reply_markup=kb, parse_mode="HTML")
    
    elif data == "dice_roll_action":
        result = game.play_dice_roll()
        amount = result['amount']
        storage.add_balance(user.id, amount)
        storage.log_play(user.id, amount, result['result'], "dice")
        storage.update_user_level(user.id)
        
        current_balance = storage.get_user_balance(user.id)
        text = f"""
🎲 <b>نتیجه رول تاس</b>

{result['message']}

💰 تغییر موجودی: {'+' if amount >= 0 else ''}{amount} سکه
💵 موجودی فعلی: {current_balance} سکه
"""
        kb = ui.after_play_markup()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # شماره خوشبخت
    elif data == "play_lucky":
        kb = ui.lucky_number_markup()
        await query.edit_message_text("✨ <b>شماره خوشبخت</b>\n\n1 از 10 شماره رو انتخاب کن:", reply_markup=kb, parse_mode="HTML")
    
    elif data.startswith("lucky_"):
        choice = int(data.split("_")[1])
        result = game.play_lucky_number(choice)
        amount = result['amount']
        storage.add_balance(user.id, amount)
        storage.log_play(user.id, amount, result['result'], "lucky")
        storage.update_user_level(user.id)
        
        current_balance = storage.get_user_balance(user.id)
        text = f"""
✨ <b>نتیجه شماره خوشبخت</b>

{result['message']}

💰 تغییر موجودی: {'+' if amount >= 0 else ''}{amount} سکه
💵 موجودی فعلی: {current_balance} سکه
"""
        kb = ui.after_play_markup()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # پرتاب سکه
    elif data == "play_coin":
        kb = ui.coin_flip_markup()
        await query.edit_message_text("🪙 <b>پرتاب سکه</b>\n\nشیر یا خط؟", reply_markup=kb, parse_mode="HTML")
    
    elif data.startswith("coin_"):
        choice = data.split("_")[1]  # heads or tails
        result = game.play_coin_flip(choice)
        amount = result['amount']
        storage.add_balance(user.id, amount)
        storage.log_play(user.id, amount, result['result'], "coin")
        storage.update_user_level(user.id)
        
        current_balance = storage.get_user_balance(user.id)
        text = f"""
🪙 <b>نتیجه پرتاب سکه</b>

{result['message']}

💰 تغییر موجودی: {'+' if amount >= 0 else ''}{amount} سکه
💵 موجودی فعلی: {current_balance} سکه
"""
        kb = ui.after_play_markup()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # پروفایل
    elif data == "profile_cb":
        stats = storage.get_user_stats(user.id)
        if stats:
            text = ui.format_user_stats(stats)
            kb = ui.back_to_menu()
            await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # موجودی
    elif data == "balance_cb":
        u = storage.create_or_get_user(user.id, update.effective_chat.id, user.full_name)
        level = storage.get_user_level(user.id)
        text = f"""
💰 <b>موجودی شما</b>

💵 مبلغ: {u['balance']} سکه
🎖️ سطح: {ui.level_emoji(level)} {ui.level_name(level)}

برای بازی‌های بیشتر به منو برو! 🎮
"""
        kb = ui.back_to_menu()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # لیدربورد
    elif data == "leaderboard_cb":
        top = storage.get_leaderboard(limit=10)
        text = ui.format_leaderboard(top)
        kb = ui.back_to_menu()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # جایزه روزانه
    elif data == "daily_cb":
        ok, amount, msg = storage.claim_daily(user.id)
        if ok:
            text = f"🎁 <b>جایزه روزانه</b>\n\n✅ {msg}\n\n💰 شما {amount} سکه دریافت کردی!"
        else:
            text = f"⏳ <b>جایزه روزانه</b>\n\n❌ {msg}"
        kb = ui.back_to_menu()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # دستاوردها
    elif data == "achievements_cb":
        achievements = storage.get_user_achievements(user.id)
        text = ui.format_achievements(achievements)
        kb = ui.back_to_menu()
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    
    # دوباره بازی
    elif data == "play_again":
        kb = ui.games_menu()
        await query.edit_message_text("🎮 <b>انتخاب بازی</b>\n\nکدام بازی رو بازی کنی؟", reply_markup=kb, parse_mode="HTML")
    
    else:
        await query.edit_message_text("❌ دستور نامشناخته.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیغام ناشناخته"""
    text = """
❓ متوجه نشدم!

لطفاً از منو استفاده کن: /menu 🎮
"""
    await update.message.reply_text(text)

def main():
    """تابع اصلی"""
    storage.ensure_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("achievements", achievements_cmd))

    # Callback Query
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # پیغام‌های ناشناخته
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    logger.info("🤖 ربات در حال اجرا است...")
    app.run_polling()

if __name__ == "__main__":
    main()
