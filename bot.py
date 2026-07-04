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
    user = update.effective_user
    storage.ensure_db()
    storage.create_or_get_user(user.id, update.effective_chat.id, user.full_name)
    await update.message.reply_text(
        "سلام 👋\nبه ربات پیشرفته خوش اومدی!\nبرای باز کردن منو /menu رو بزن."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ui.main_menu()
    await update.message.reply_text("منو:", reply_markup=kb)

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = storage.create_or_get_user(user.id, update.effective_chat.id, user.full_name)
    await update.message.reply_text(f"💰 موجودی شما: {u['balance']} سکه")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = storage.get_leaderboard(limit=10)
    text = "🏆 لیدربورد:\n"
    for i, row in enumerate(top, start=1):
        text += f"{i}. {row['name']} — {row['balance']} سکه\n"
    await update.message.reply_text(text)

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ok, amount, msg = storage.claim_daily(user.id)
    if ok:
        await update.message.reply_text(f"🎁 جایزه روزانه: {amount} سکه\n{msg}")
    else:
        await update.message.reply_text(msg)

async def miniapp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ui.play_menu()
    await update.message.reply_text("مینی‌اپ: Coin Collector\nیک صندوق انتخاب کن:", reply_markup=kb)

async def setbalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # admin command: /setbalance <user_id> <amount>
    user = update.effective_user
    if not getattr(config, "ADMINS", None) or user.id not in config.ADMINS:
        await update.message.reply_text("شما دسترسی لازم برای این دستور را ندارید.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استفاده: /setbalance <user_id> <amount>")
        return
    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("شناسه یا مقدار ناصحیح است.")
        return
    storage.set_balance(target_id, amount)
    await update.message.reply_text(f"موجودی کاربر {target_id} روی {amount} تنظیم شد.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    if data.startswith("play_"):
        # show chests
        kb = ui.chests_markup()
        await query.edit_message_text("یکی از 3 صندوق رو انتخاب کن:", reply_markup=kb)
    elif data.startswith("chest_"):
        # cooldown check
        ok, rem = storage.can_play(user.id)
        if not ok:
            await query.answer(text=f"لطفا {int(rem)} ثانیه دیگر صبر کنید.", show_alert=True)
            return
        choice = int(data.split("_")[1])
        result = game.open_chest(user.id, choice)
        storage.add_balance(user.id, result["amount"])
        storage.log_play(user.id, result["amount"], result["outcome"])
        text = f"🎯 نتیجه: {result['outcome_text']}\n\nتغییر موجودی: {result['amount']} سکه\nموجودی فعلی: {storage.get_user_balance(user.id)} سکه"
        kb = ui.after_play_markup()
        await query.edit_message_text(text, reply_markup=kb)
    elif data == "balance_cb":
        await query.edit_message_text(f"💰 موجودی شما: {storage.get_user_balance(user.id)} سکه")
    elif data == "leaderboard_cb":
        top = storage.get_leaderboard(limit=10)
        text = "🏆 لیدربورد:\n"
        for i, row in enumerate(top, start=1):
            text += f"{i}. {row['name']} — {row['balance']} سکه\n"
        await query.edit_message_text(text)
    elif data == "daily_cb":
        ok, amount, msg = storage.claim_daily(user.id)
        if ok:
            await query.edit_message_text(f"🎁 جایزه روزانه: {amount} سکه\n{msg}")
        else:
            await query.edit_message_text(msg)
    elif data == "back_menu":
        kb = ui.main_menu()
        await query.edit_message_text("منو:", reply_markup=kb)
    elif data == "play_again":
        kb = ui.chests_markup()
        await query.edit_message_text("یکی دیگر از 3 صندوق رو انتخاب کن:", reply_markup=kb)
    else:
        await query.edit_message_text("عمل نامشخص.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("متوجه نشدم؛ از /menu استفاده کن.")

def main():
    storage.ensure_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("miniapp", miniapp_cmd))
    app.add_handler(CommandHandler("setbalance", setbalance_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
