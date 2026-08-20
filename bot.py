import logging
import time
import requests
import sqlite3
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== КОНФИГИ =====
TOKEN = "8984654579:AAGaUlKtAjJd7wqR5BsaLEBMUeGKmztC-pM"
NOWPAYMENTS_API_KEY = "438GJF7-CF747JD-G38BH6E-QZ1C7YD"
MONERO_ADDRESS = "46r6fC7DptBgov3ZQPtdzJ8Ge8o1fDiqe8UPPm1BxDLC4iHrFwn32PUWTXz3qH8jdaRMzuXG3obCdEbNncoJfMDHRMQ4N91"
USDT_ADDRESS = "TEmyv3w1CjftMMbF4qxEffV8P2P3D9m8xa"
FILE_URL = "https://tmpfiles.org/wRwDSeA58F4E/blackout.exe"
ADMIN_USER = "admin"
ADMIN_PASS = "swill2026"
ADMIN_CHAT_ID = "8640296115"

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        phone TEXT,
        telegram_id TEXT,
        password TEXT,
        created_at TEXT
    )''')
    # Таблица заказов
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        amount REAL,
        paid INTEGER DEFAULT 0,
        license_key TEXT,
        file_url TEXT,
        payment_id TEXT,
        created_at TEXT
    )''')
    # Таблица статистики
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_sms INTEGER DEFAULT 0,
        total_bots INTEGER DEFAULT 0,
        total_sites INTEGER DEFAULT 0
    )''')
    conn.commit()

    try:
        c.execute("ALTER TABLE users ADD COLUMN telegram_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO stats (total_sms, total_bots, total_sites) VALUES (15230, 8, 5)")

    conn.commit()
    conn.close()

def add_user(username, email, phone, password):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, email, phone, password, created_at) VALUES (?, ?, ?, ?, ?)",
              (username, email, phone, password, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_telegram_id(telegram_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_telegram_id(username, telegram_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("UPDATE users SET telegram_id=? WHERE username=?", (telegram_id, username))
    conn.commit()
    conn.close()

def add_order(user_id, plan, amount, payment_id):
    license_key = generate_license()
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, plan, amount, license_key, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, plan, amount, license_key, payment_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return license_key

def get_orders_by_user(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_paid(order_id, file_url):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("UPDATE orders SET paid=1, file_url=? WHERE id=?", (file_url, order_id))
    conn.commit()
    conn.close()

def get_order_by_payment_id(payment_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, license_key FROM orders WHERE payment_id=? AND paid=0", (payment_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def generate_license():
    parts = []
    for _ in range(3):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return f"BLACKOUT-{'-'.join(parts)}"

# ===== NOWPAYMENTS =====
def create_nowpayments_payment(amount, order_id, user_id):
    url = "https://api.nowpayments.io/v1/payment"
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": amount,
        "price_currency": "usd",
        "pay_currency": "usdtrc20",
        "order_id": f"order_{order_id}",
        "order_description": f"user_{user_id}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ===== FLASK ПРИЛОЖЕНИЕ =====
app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        if get_user_by_username(username):
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        add_user(username, email, phone, password)
        flash('Регистрация успешна! Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and user[4] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    orders = get_orders_by_user(session['user_id'])
    return render_template('dashboard.html', user=user, orders=orders)

@app.route('/buy/<plan>')
def buy(plan):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    prices = {'lite': 99, 'pro': 299, 'enterprise': 999}
    if plan not in prices:
        return "Неверный тариф", 400
    amount = prices[plan]
    user_id = session['user_id']
    order_id = random.randint(100000, 999999)
    license_key = add_order(user_id, plan, amount, f"order_{order_id}")
    payment = create_nowpayments_payment(amount, order_id, user_id)
    if 'invoice_url' in payment:
        return render_template('payment.html', payment_url=payment['invoice_url'], plan=plan, amount=amount)
    else:
        return "Ошибка создания платежа", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===== WEBHOOK =====
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get('payment_status') == 'finished':
        payment_id = data.get('order_id')
        if payment_id:
            order = get_order_by_payment_id(payment_id)
            if order:
                order_id, user_id, license_key = order
                mark_paid(order_id, FILE_URL)
                import requests as req
                user = get_user_by_id(user_id)
                if user and user[5]:
                    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    payload = {
                        'chat_id': user[5],
                        'text': f"✅ Оплата подтверждена!\n🔑 Лицензия: `{license_key}`\n📥 Ссылка: {FILE_URL}",
                        'parse_mode': 'Markdown'
                    }
                    req.post(url, json=payload)
                return jsonify({"ok": True}), 200
    return jsonify({"error": "invalid"}), 400

# ===== TELEGRAM БОТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user_by_telegram_id(str(user_id))
    if not user:
        await update.message.reply_text(
            "👋 Привет! У вас нет аккаунта на сайте.\n"
            "Пожалуйста, зарегистрируйтесь сначала на сайте:\n"
            "https://rtyt232.github.io/portfolio/register"
        )
        return
    keyboard = [
        [InlineKeyboardButton("Купить Lite — $99", callback_data="buy_lite")],
        [InlineKeyboardButton("Купить Pro — $299", callback_data="buy_pro")],
        [InlineKeyboardButton("Купить Enterprise — $999", callback_data="buy_enterprise")],
        [InlineKeyboardButton("🌐 Сайт", callback_data="site")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Добро пожаловать в Swill Monitor!", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "site":
        await query.edit_message_text("🌐 Сайт: https://rtyt232.github.io/portfolio/")
    elif data.startswith("buy_"):
        plan = data.replace("buy_", "")
        prices = {'lite': 99, 'pro': 299, 'enterprise': 999}
        if plan not in prices:
            await query.edit_message_text("❌ Неизвестный тариф.")
            return
        amount = prices[plan]
        await query.edit_message_text(
            f"💰 {plan.upper()} — ${amount}\n\n"
            f"Для оплаты перейдите на сайт и авторизуйтесь:\n"
            f"https://rtyt232.github.io/portfolio/"
        )

def run_bot():
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен!")
    app_bot.run_polling()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    init_db()
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
