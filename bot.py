import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== ТВОЙ ТОКЕН ==========
TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"

# ========== КОМАНДА /start ==========
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
        "Я — бот для заказа IT-услуг:\n"
        "• Telegram-боты\n"
        "• Сайты и лендинги\n"
        "• SMS-рассылки по всему миру\n"
        "• Автоматизация и парсинг\n\n"
        "Выберите тариф или перейдите на сайт:",
        reply_markup=reply_markup
    )

# ========== ОБРАБОТКА КНОПОК ==========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "site":
        await query.edit_message_text(
            "🌐 Мой сайт-визитка:\n"
            "https://RTYT232.github.io/portfolio/\n\n"
            "Там всё: что я делаю, цены, примеры работ.\n"
            "Заказы принимаю здесь — @RATNIKIPCbot"
        )

    elif data == "buy_lite":
        await query.edit_message_text(
            "💰 Тариф Lite — $99\n\n"
            "✅ До 5 устройств\n"
            "✅ Базовый сбор логов\n"
            "✅ Скрытый режим\n"
            "✅ Автозапуск\n\n"
            "Оплата: Monero (XMR) или USDT\n"
            "После оплаты — ссылка на скачивание."
        )

    elif data == "buy_pro":
        await query.edit_message_text(
            "💰 Тариф Pro — $299\n\n"
            "✅ До 20 устройств\n"
            "✅ Обход Defender\n"
            "✅ Удалённый шелл\n"
            "✅ ICMP-туннель\n"
            "✅ Приоритетная поддержка\n\n"
            "Оплата: Monero (XMR) или USDT"
        )

    elif data == "buy_enterprise":
        await query.edit_message_text(
            "💰 Тариф Enterprise — $999\n\n"
            "✅ Безлимит устройств\n"
            "✅ UEFI-персистентность\n"
            "✅ Полиморфный билд\n"
            "✅ Обход EDR\n"
            "✅ Индивидуальная поддержка 24/7\n\n"
            "Оплата: Monero (XMR) или USDT"
        )

    elif data == "instructions":
        await query.edit_message_text(
            "📖 Инструкция по установке:\n\n"
            "1️⃣ Скачайте .exe файл по ссылке\n"
            "2️⃣ Добавьте в исключения антивируса\n"
            "3️⃣ Запустите от имени администратора\n"
            "4️⃣ Агент установится и запустится в фоне\n\n"
            "Если проблемы — напишите /support"
        )

    elif data == "support":
        await query.edit_message_text(
            "🛠 Поддержка\n\n"
            "Напишите ваш вопрос прямо в этот чат.\n"
            "Я отвечу вручную в течение 12 часов."
        )

    else:
        await query.edit_message_text("❌ Неизвестная команда.")

# ========== ЗАПУСК БОТА ==========
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
