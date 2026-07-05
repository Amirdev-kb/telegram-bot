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
            streak INTEGER DEFAULT 0,
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
        
        # جدول دستاوردها
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
        
        # جدول چالش‌های روزانه
        c.execute("""
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_type TEXT,
            target INTEGER,
            progress INTEGER DEFAULT 0,
            reward INTEGER,
            completed INTEGER DEFAULT 0,
            date TEXT
        )""")
        
        # جدول بانک
        c.execute("""
        CREATE TABLE IF NOT EXISTS bank (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            deposit INTEGER DEFAULT 0,
            interest_rate REAL DEFAULT 0.5,
            last_interest TEXT
        )""")
        
        # جدول دوستی
        c.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_1 INTEGER,
            user_id_2 INTEGER,
            created_at TEXT
        )""")
        
        conn.commit()
        conn.close()

def create_or_get_user(user_id, chat_id, name):
    """ایجاد یا دریافت کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT user_id, chat_id, name, balance, level, total_wins, total_losses, last_daily, streak 
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
                "last_daily": row[7],
                "streak": row[8]
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
                "last_daily": None,
                "streak": 0
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
            c.execute("UPDATE users SET total_wins = total_wins + 1, streak = streak + 1 WHERE user_id = ?", (user_id,))
        else:
            c.execute("UPDATE users SET total_losses = total_losses + 1, streak = 0 WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()

def get_leaderboard(limit=15):
    """دریافت جدول امتیازات"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT name, balance, level, total_wins, streak FROM users 
                     ORDER BY balance DESC LIMIT ?""", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"name": r[0], "balance": r[1], "level": r[2], "wins": r[3], "streak": r[4]} for r in rows]

def claim_daily(user_id):
    """دریافت جایزه روزانه"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("SELECT last_daily, streak FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, 0, "کاربر پیدا نشد."
        
        last = row[0]
        streak = row[1]
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
        # بونوس برای استریک
        streak_bonus = min(streak * 5, 100)
        total_amount = amount + streak_bonus
        
        c.execute("""UPDATE users SET balance = balance + ?, last_daily = ? 
                     WHERE user_id = ?""", (total_amount, now.isoformat(), user_id))
        
        # ثبت تراکنش
        c.execute("""INSERT INTO transactions (user_id, type, amount, reason, timestamp) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, "income", total_amount, "daily_reward", now.isoformat()))
        
        conn.commit()
        conn.close()
        
        msg = f"{amount} سکه + {streak_bonus} بونوس استریک" if streak_bonus > 0 else f"{amount} سکه"
        return True, total_amount, f"✅ جایزه روزانه: {msg}"

def get_user_stats(user_id):
    """دریافت آمار کاربر"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT name, balance, level, total_wins, total_losses, created_at, streak 
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
            "created_at": row[5],
            "streak": row[6]
        }

def get_detailed_stats(user_id):
    """دریافت آمار تفصیلی"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        
        # اطلاعات کلی
        c.execute("""SELECT total_wins, total_losses FROM users WHERE user_id = ?""", (user_id,))
        row = c.fetchone()
        total_wins = row[0] if row else 0
        total_losses = row[1] if row else 0
        total_games = total_wins + total_losses
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        # درآمد و هزینه
        c.execute("""SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'""", (user_id,))
        total_income = c.fetchone()[0] or 0
        
        c.execute("""SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'""", (user_id,))
        total_spent = c.fetchone()[0] or 0
        
        # بهترین و بدترین
        c.execute("""SELECT MAX(amount) FROM plays WHERE user_id = ? AND amount > 0""", (user_id,))
        best_win = c.fetchone()[0] or 0
        
        c.execute("""SELECT MIN(amount) FROM plays WHERE user_id = ? AND amount < 0""", (user_id,))
        worst_loss = c.fetchone()[0] or 0
        
        # بازی مورد علاقه
        c.execute("""SELECT game_type FROM plays WHERE user_id = ? GROUP BY game_type ORDER BY COUNT(*) DESC LIMIT 1""", (user_id,))
        favorite_game = c.fetchone()[0] or "نامعلوم"
        
        conn.close()
        
        return {
            "total_games": total_games,
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": f"{win_rate:.1f}%",
            "total_income": total_income,
            "total_spent": total_spent,
            "net": total_income - total_spent,
            "best_win": best_win,
            "worst_loss": worst_loss,
            "favorite_game": favorite_game
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

def get_daily_challenge(user_id):
    """دریافت چالش روزانه"""
    ensure_db()
    today = datetime.utcnow().date().isoformat()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT challenge_type, target, progress, reward, completed FROM daily_challenges 
                     WHERE user_id = ? AND date = ?""", (user_id, today))
        row = c.fetchone()
        
        if not row:
            # ایجاد چالش جدید
            import random
            challenge_types = {
                "wins": {"description": "۵ بار برنده شو", "target": 5},
                "games": {"description": "۱۰ بازی بازی کن", "target": 10},
                "streak": {"description": "۳ بار پی‌در‌پی برنده شو", "target": 3},
            }
            challenge_type = random.choice(list(challenge_types.keys()))
            target = challenge_types[challenge_type]["target"]
            reward = 100
            
            c.execute("""INSERT INTO daily_challenges (user_id, challenge_type, target, reward, date) 
                         VALUES (?, ?, ?, ?, ?)""",
                     (user_id, challenge_type, target, reward, today))
            conn.commit()
            
            return {
                "description": challenge_types[challenge_type]["description"],
                "target": target,
                "progress": 0,
                "reward": reward,
                "completed": False
            }
        
        conn.close()
        return {
            "description": row[0],
            "target": row[1],
            "progress": row[2],
            "reward": row[3],
            "completed": bool(row[4])
        }

def get_bank_info(user_id):
    """دریافت اطلاعات بانک"""
    ensure_db()
    with _lock:
        conn = _conn()
        c = conn.cursor()
        c.execute("""SELECT balance, deposit, interest_rate, last_interest FROM bank WHERE user_id = ?""", (user_id,))
        row = c.fetchone()
        
        if not row:
            c.execute("""INSERT INTO bank (user_id) VALUES (?)""", (user_id,))
            conn.commit()
            conn.close()
            return {
                "balance": 0,
                "deposit": 0,
                "interest": 0.5,
                "interest_ready": False
            }
        
        conn.close()
        
        last_interest = row[3]
        now = datetime.utcnow()
        interest_ready = False
        
        if last_interest:
            last_dt = datetime.fromisoformat(last_interest)
            if now - last_dt >= timedelta(hours=24):
                interest_ready = True
        else:
            interest_ready = True
        
        return {
            "balance": row[0],
            "deposit": row[1],
            "interest": row[2],
            "interest_ready": interest_ready
        }
