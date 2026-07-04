import random
from datetime import datetime

# ساده و قابل تنظیم: سه صندوق، احتمال‌ها/جوایز
CHESTS = [
    {"id": 1, "prob": 0.15, "amount": 200, "text": "جایزه بزرگ!"},
    {"id": 2, "prob": 0.65, "amount": 50, "text": "پول کمی پیدا شد."},
    {"id": 3, "prob": 0.20, "amount": -30, "text": "تله! خسارت خوردی."},
]

def _choose_chest():
    r = random.random()
    s = 0.0
    for ch in CHESTS:
        s += ch["prob"]
        if r <= s:
            return ch
    return CHESTS[-1]

def open_chest(user_id, choice_index):
    # choice_index: 1,2,3 (برای نمایش) — ولی نتیجه بر اساس احتمالات تولید میشه
    chest = _choose_chest()
    amount = chest["amount"]
    outcome = "win" if amount > 0 else "lose"
    outcome_text = f"{chest['text']} ({'+' if amount>0 else ''}{amount} سکه)"
    return {
        "user_id": user_id,
        "choice": choice_index,
        "amount": amount,
        "outcome": outcome,
        "outcome_text": outcome_text,
        "timestamp": datetime.utcnow().isoformat(),
    }
