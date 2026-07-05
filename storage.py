import sqlite3
import threading
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DB_PATH = "bot.db"
_lock = threading.Lock()

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_db():
    """ایجاد جداول مورد نیاز"""
    with _lock:
        conn = _conn()
        c = conn.cursor()
        
        # جدول کاربران
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            name TEXT,
            balance INTEGER DEFAULT 200,
            level INTEGER DEFAULT 1,
            total_wins INTEGER DEFAULT 0,
            total_losses INTEGER DEFAULT 0,
            last_daily TEXT,
            created_at TEXT,
            updated_at TEXT
        )""")
        
        # جدول بازی‌ها
        c.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT,
            amount INTEGER,
            outcome TEXT,
            timestamp TEXT
        )""")
        
        # جدول مختارهای شامل
        c.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_name TEXT,
            description TEXT,
            unlocked_at TEXT
        )""")
        
        # جدول تراکنش‌ها
        c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount INTEGER,
            reason TEXT,
            timestamp TEXT
        )""")
        
        conn.commit()
        conn.close()

def create_or_get_user(user_id, chat_id, name):
    """ایجاد یا دریافت کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT user_id, chat_id, name, balance, level, total_wins, total_losses, last_daily 
                     FROM users WHERE user_id=?""", (user_id,))
        row = c.fetchone()
        if row:
            user = {
                "user_id": row[0],
                "chat_id": row[1],
                "name": row[2],
                "balance": row[3],
                "level": row[4],
                "total_wins": row[5],
                "total_losses": row[6],
                "last_daily": row[7]
            }
        else:
            now = datetime.utcnow().isoformat()
            c.execute("""INSERT INTO users (user_id, chat_id, name, balance, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?)""", 
                     (user_id, chat_id, name, 200, now, now))
            conn.commit()
            user = {
                "user_id": user_id,
                "chat_id": chat_id,
                "name": name,
                "balance": 200,
                "level": 1,
                "total_wins": 0,
                "total_losses": 0,
                "last_daily": None
            }
        conn.close()
        return user

def add_balance(user_id, amount):
    """اضافه کردن موجودی"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        
        # ثبت تراکنش
        c.execute("""INSERT INTO transactions (user_id, type, amount, reason, timestamp) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, "income" if amount > 0 else "expense", abs(amount), "game_result", datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

def get_user_balance(user_id):
    """دریافت موجودی کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

def get_user_level(user_id):
    """دریافت سطح کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 1

def update_user_level(user_id):
    """به‌روزرسانی سطح کاربر بر اساس موجودی"""
    balance = get_user_balance(user_id)
    if balance < 500:
        level = 1
    elif balance < 2000:
        level = 2
    elif balance < 5000:
        level = 3
    elif balance < 10000:
        level = 4
    else:
        level = 5
    
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
        conn.commit()
        conn.close()

def log_play(user_id, amount, outcome, game_type="chest"):
    """ثبت بازی"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        
        # ثبت بازی
        c.execute("""INSERT INTO plays (user_id, game_type, amount, outcome, timestamp) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, game_type, amount, outcome, datetime.utcnow().isoformat()))
        
        # به‌روزرسانی آمار برد/باخت
        if outcome == "win":
            c.execute("UPDATE users SET total_wins = total_wins + 1 WHERE user_id = ?", (user_id,))
        else:
            c.execute("UPDATE users SET total_losses = total_losses + 1 WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()

def get_leaderboard(limit=10):
    """دریافت جدول امتیازات"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT name, balance, level, total_wins FROM users 
                     ORDER BY balance DESC LIMIT ?""", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"name": r[0], "balance": r[1], "level": r[2], "wins": r[3]} for r in rows]

def claim_daily(user_id):
    """دریافت جایزه روزانه"""
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
                return False, 0, f"⏳ تا {h} ساعت و {m} دقیقه دیگر می‌توانی جایزه روزانه بگیری."
        
        # اعطای جایزه
        amount = 50
        c.execute("""UPDATE users SET balance = balance + ?, last_daily = ? 
                     WHERE user_id = ?""", (amount, now.isoformat(), user_id))
        
        # ثبت تراکنش
        c.execute("""INSERT INTO transactions (user_id, type, amount, reason, timestamp) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, "income", amount, "daily_reward", now.isoformat()))
        
        conn.commit()
        conn.close()
        return True, amount, f"🎁 جایزه روزانه: {amount} سکه"

def get_user_stats(user_id):
    """دریافت آمار کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT name, balance, level, total_wins, total_losses, created_at 
                     FROM users WHERE user_id = ?""", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        total_games = row[3] + row[4]
        win_rate = (row[3] / total_games * 100) if total_games > 0 else 0
        
        return {
            "name": row[0],
            "balance": row[1],
            "level": row[2],
            "total_wins": row[3],
            "total_losses": row[4],
            "total_games": total_games,
            "win_rate": f"{win_rate:.1f}%",
            "created_at": row[5]
        }

def unlock_achievement(user_id, achievement_name, description):
    """باز کردن دستاورد"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        
        # بررسی دستاورد قبلی
        c.execute("""SELECT id FROM achievements 
                     WHERE user_id = ? AND achievement_name = ?""", (user_id, achievement_name))
        if c.fetchone():
            conn.close()
            return False
        
        # افزودن دستاورد
        c.execute("""INSERT INTO achievements (user_id, achievement_name, description, unlocked_at) 
                     VALUES (?, ?, ?, ?)""",
                 (user_id, achievement_name, description, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        return True

def get_user_achievements(user_id):
    """دریافت دستاوردهای کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT achievement_name, description FROM achievements 
                     WHERE user_id = ? ORDER BY unlocked_at DESC""", (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"name": r[0], "description": r[1]} for r in rows]
