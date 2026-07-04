import sqlite3
import threading
from datetime import datetime, timedelta
import csv

DB_PATH = "bot.db"
_lock = threading.Lock()

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_db():
    with _lock:
        conn = _conn()
        c = conn.cursor()
        # create users table if not exists
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            name TEXT,
            balance INTEGER DEFAULT 0,
            last_daily TEXT,
            last_play TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            outcome TEXT,
            timestamp TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item_key TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, item_key)
        )""")
        conn.commit()
        conn.close()

# User helpers
def create_or_get_user(user_id, chat_id, name):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT user_id, chat_id, name, balance, last_daily, last_play FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            user = {"user_id": row[0], "chat_id": row[1], "name": row[2], "balance": row[3], "last_daily": row[4], "last_play": row[5]}
        else:
            c.execute("INSERT INTO users (user_id, chat_id, name, balance) VALUES (?, ?, ?, ?)", (user_id, chat_id, name, 100))
            conn.commit()
            user = {"user_id": user_id, "chat_id": chat_id, "name": name, "balance": 100, "last_daily": None, "last_play": None}
        conn.close()
        return user

def add_balance(user_id, amount):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

def set_balance(user_id, amount):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

def get_user_balance(user_id):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

# Plays
def log_play(user_id, amount, outcome):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        c.execute("INSERT INTO plays (user_id, amount, outcome, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, amount, outcome, timestamp))
        # update last_play
        c.execute("UPDATE users SET last_play = ? WHERE user_id = ?", (timestamp, user_id))
        conn.commit()
        conn.close()

def get_leaderboard(limit=10):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"name": r[0], "balance": r[1]} for r in rows]

def claim_daily(user_id):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, 0, "کاربر پیدا نشد."
        last = row[0]
        now = datetime.utcnow()
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_dt)
                h = remaining.seconds // 3600
                m = (remaining.seconds % 3600) // 60
                conn.close()
                return False, 0, f"شما قبلاً جایزه روزانه رو گرفتید. تا {h} ساعت و {m} دقیقه دیگر قابل دریافت است."
        # award
        amount = 50  # مقدار جایزه روزانه
        c.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (amount, now.isoformat(), user_id))
        conn.commit()
        conn.close()
        return True, amount, "موفقیت‌آمیز! جایزه به حساب شما افزوده شد."

# Cooldown
def can_play(user_id, min_seconds: int = 5):
    """Return (True, 0) if user can play, otherwise (False, seconds_remaining)."""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT last_play FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if not row or not row[0]:
            return True, 0
        last = datetime.fromisoformat(row[0])
        now = datetime.utcnow()
        diff = (now - last).total_seconds()
        if diff >= min_seconds:
            return True, 0
        else:
            return False, int(min_seconds - diff)

# Shop / Inventory
SHOP_ITEMS = {
    "lucky_key": {"key": "lucky_key", "name": "🎲 کلید شانس", "desc": "شانس جایزه بزرگ را برای یک بازی افزایش می‌دهد.", "price": 200},
    "shield": {"key": "shield", "name": "🛡️ شیلد", "desc": "یک بار از جریمه جلوگیری می‌کند.", "price": 150},
}

def get_shop_items():
    return list(SHOP_ITEMS.values())

def get_inventory(user_id):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT item_key, count FROM inventory WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

def buy_item(user_id, item_key):
    ensure_db()
    if item_key not in SHOP_ITEMS:
        return False, "آیتم نامعتبر است."
    price = SHOP_ITEMS[item_key]["price"]
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, "کاربر پیدا نشد."
        if row[0] < price:
            conn.close()
            return False, "موجودی کافی نیست."
        # deduct
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        # upsert inventory
        c.execute("SELECT count FROM inventory WHERE user_id = ? AND item_key = ?", (user_id, item_key))
        r = c.fetchone()
        if r:
            c.execute("UPDATE inventory SET count = count + 1 WHERE user_id = ? AND item_key = ?", (user_id, item_key))
        else:
            c.execute("INSERT INTO inventory (user_id, item_key, count) VALUES (?, ?, 1)", (user_id, item_key))
        conn.commit()
        conn.close()
        return True, f"خرید موفق: {SHOP_ITEMS[item_key]['name']}"

def consume_item(user_id, item_key):
    """Consume one item from inventory. Return True if consumed, False otherwise."""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT count FROM inventory WHERE user_id = ? AND item_key = ?", (user_id, item_key))
        r = c.fetchone()
        if not r or r[0] <= 0:
            conn.close()
            return False
        c.execute("UPDATE inventory SET count = count - 1 WHERE user_id = ? AND item_key = ?", (user_id, item_key))
        conn.commit()
        conn.close()
        return True

# Admin / utilities
def add_coins(user_id, amount):
    return add_balance(user_id, amount)

def export_data(csv_path="export.csv"):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        # export users
        c.execute("SELECT user_id, name, balance, last_daily, last_play FROM users")
        users = c.fetchall()
        c.execute("SELECT id, user_id, amount, outcome, timestamp FROM plays")
        plays = c.fetchall()
        conn.close()
    with open(csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["users"])
        writer.writerow(["user_id", "name", "balance", "last_daily", "last_play"])
        for u in users:
            writer.writerow(u)
        writer.writerow([])
        writer.writerow(["plays"])
        writer.writerow(["id", "user_id", "amount", "outcome", "timestamp"])
        for p in plays:
            writer.writerow(p)
    return csv_path

def reset_db():
    """Dangerous admin operation: drops all tables and recreates schema."""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS plays")
        c.execute("DROP TABLE IF EXISTS inventory")
        c.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        conn.close()
    # recreate
    ensure_db()
