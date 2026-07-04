import sqlite3
import threading
from datetime import datetime, timedelta

DB_PATH = "bot.db"
_lock = threading.Lock()

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_db():
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            name TEXT,
            balance INTEGER DEFAULT 0,
            last_daily TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            outcome TEXT,
            timestamp TEXT
        )""")
        conn.commit()
        conn.close()

def create_or_get_user(user_id, chat_id, name):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT user_id, chat_id, name, balance, last_daily FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            user = {"user_id": row[0], "chat_id": row[1], "name": row[2], "balance": row[3], "last_daily": row[4]}
        else:
            c.execute("INSERT INTO users (user_id, chat_id, name, balance) VALUES (?, ?, ?, ?)", (user_id, chat_id, name, 100))
            conn.commit()
            user = {"user_id": user_id, "chat_id": chat_id, "name": name, "balance": 100, "last_daily": None}
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

def get_user_balance(user_id):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

def log_play(user_id, amount, outcome):
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("INSERT INTO plays (user_id, amount, outcome, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, amount, outcome, datetime.utcnow().isoformat()))
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
