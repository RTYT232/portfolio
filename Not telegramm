import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить Lite — $99", callback_data="buy_lite")],
        [InlineKeyboardButton("Купить Pro — $299", callback_data="buy_pro")],
        [InlineKeyboardButton("Купить Enterprise — $999", callback_data="buy_enterprise")],
        [InlineKeyboardButton("🌐 Сайт", callback_data="site")],
    ]
    await update.message.reply_text(
        "👋 Добро пожаловать в Swill Monitor!\nВыберите тариф:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "site":
        await query.edit_message_text(
            "🌐 Мой сайт-визитка:\nhttps://RTYT232.github.io/portfolio/\n\nТам всё: что я делаю, цены, примеры работ."
        )
    elif data == "buy_lite":
        await query.edit_message_text("💰 Lite — $99\nОплата: Monero или USDT")
    elif data == "buy_pro":
        await query.edit_message_text("💰 Pro — $299\nОплата: Monero или USDT")
    elif data == "buy_enterprise":
        await query.edit_message_text("💰 Enterprise — $999\nОплата: Monero или USDT")
    else:
        await query.edit_message_text("Неизвестная команда.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
