import random
from datetime import datetime
import storage

# ساده و قابل تنظیم: سه صندوق، احتمال‌ها/جوایز
CHESTS = [
    {"id": 1, "prob": 0.15, "amount": 200, "text": "جایزه بزرگ!"},
    {"id": 2, "prob": 0.65, "amount": 50, "text": "پول کمی پیدا شد."},
    {"id": 3, "prob": 0.20, "amount": -30, "text": "تله! خسارت خوردی."},
]

def _choose_chest(custom_probs=None):
    # custom_probs is a list of probs matching CHESTS order
    probs = [c['prob'] for c in CHESTS]
    if custom_probs:
        probs = custom_probs
    total = sum(probs)
    r = random.random() * total
    s = 0.0
    for i, p in enumerate(probs):
        s += p
        if r <= s:
            return CHESTS[i]
    return CHESTS[-1]

def open_chest(user_id, choice_index):
    # Check for lucky_key: if present, consume and boost big-chest chance
    consumed_lucky = storage.consume_item(user_id, 'lucky_key')
    if consumed_lucky:
        # boost big chest probability
        custom = [0.6, 0.3, 0.1]
        chest = _choose_chest(custom_probs=custom)
    else:
        chest = _choose_chest()
    amount = chest["amount"]
    outcome = "win" if amount > 0 else "lose"
    outcome_text = f"{chest['text']} ({'+' if amount>0 else ''}{amount} سکه)"
    # If negative and user has shield, consume it to prevent loss
    if amount < 0:
        consumed_shield = storage.consume_item(user_id, 'shield')
        if consumed_shield:
            amount = 0
            outcome = 'shield'
            outcome_text = "شما شیلد داشتید — از جریمه جلوگیری شد! (0 سکه)"
    return {
        "user_id": user_id,
        "choice": choice_index,
        "amount": amount,
        "outcome": outcome,
        "outcome_text": outcome_text,
        "timestamp": datetime.utcnow().isoformat(),
    }
