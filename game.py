import random
from datetime import datetime

# ساده و قابل تنظیم: سه صندوق، احتمال‌ها/جوایز
CHESTS = [
    {"id": 1, "prob": 0.15, "amount": 200, "text": "جایزه بزرگ!"},
    {"id": 2, "prob": 0.65, "amount": 50, "text": "پول کمی پیدا شد."},
    {"id": 3, "prob": 0.20, "amount": -30, "text": "تله! خسارت خوردی."},
]

# بازی‌های اضافی
MULTIPLAYER_GAMES = {
    "dice_roll": {
        "name": "رول تاس",
        "description": "شانس برنده شدن: ۵۰%",
        "base_reward": 100,
        "win_multiplier": 2,
    },
    "lucky_number": {
        "name": "شماره خوشبخت",
        "description": "۱ از ۱۰ شماره را انتخاب کن",
        "base_reward": 150,
        "win_multiplier": 5,
    },
    "coin_flip": {
        "name": "پرتاب سکه",
        "description": "شیر یا خط؟",
        "base_reward": 75,
        "win_multiplier": 2,
    },
    "roulette": {
        "name": "چرخ بختیار",
        "description": "قرمز یا سیاه؟",
        "base_reward": 100,
        "win_multiplier": 2,
    },
    "card_game": {
        "name": "بازی کارتی",
        "description": "کارت بالاتر انتخاب کن",
        "base_reward": 120,
        "win_multiplier": 3,
    },
}

def _choose_chest():
    """انتخاب صندوق بر اساس احتمالات"""
    r = random.random()
    s = 0.0
    for ch in CHESTS:
        s += ch["prob"]
        if r <= s:
            return ch
    return CHESTS[-1]

def open_chest(user_id, choice_index):
    """باز کردن صندوق"""
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

def play_dice_roll():
    """بازی رول تاس"""
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        return {
            "result": "win",
            "amount": MULTIPLAYER_GAMES["dice_roll"]["base_reward"] * MULTIPLAYER_GAMES["dice_roll"]["win_multiplier"],
            "message": f"🎲 شما: {player_roll} | ربات: {bot_roll}\nتو برنده شدی! 🎉",
        }
    elif player_roll < bot_roll:
        return {
            "result": "lose",
            "amount": -MULTIPLAYER_GAMES["dice_roll"]["base_reward"],
            "message": f"🎲 شما: {player_roll} | ربات: {bot_roll}\nربات برنده شد! 😢",
        }
    else:
        return {
            "result": "draw",
            "amount": 0,
            "message": f"🎲 برابر! {player_roll} = {bot_roll}",
        }

def play_lucky_number(user_choice):
    """بازی شماره خوشبخت"""
    lucky = random.randint(1, 10)
    
    if user_choice == lucky:
        return {
            "result": "win",
            "amount": MULTIPLAYER_GAMES["lucky_number"]["base_reward"] * MULTIPLAYER_GAMES["lucky_number"]["win_multiplier"],
            "message": f"✨ شماره خوشبخت: {lucky}\nآفرین! 🎉 برنده شدی!",
        }
    else:
        return {
            "result": "lose",
            "amount": -MULTIPLAYER_GAMES["lucky_number"]["base_reward"],
            "message": f"✨ شماره خوشبخت: {lucky}\nشماره درستی نبود! 😢",
        }

def play_coin_flip(user_choice):
    """بازی پرتاب سکه"""
    result = random.choice(["heads", "tails"])
    result_text = "شیر" if result == "heads" else "خط"
    user_choice_text = "شیر" if user_choice == "heads" else "خط"
    
    if user_choice == result:
        return {
            "result": "win",
            "amount": MULTIPLAYER_GAMES["coin_flip"]["base_reward"] * MULTIPLAYER_GAMES["coin_flip"]["win_multiplier"],
            "message": f"🪙 نتیجه: {result_text}\nتو درست حدس زدی! 🎉",
        }
    else:
        return {
            "result": "lose",
            "amount": -MULTIPLAYER_GAMES["coin_flip"]["base_reward"],
            "message": f"🪙 نتیجه: {result_text}\nمتأسفانه اشتباه شد! 😢",
        }

def play_roulette(user_choice):
    """بازی چرخ بختیار"""
    result = random.choice(["red", "black"])
    result_text = "قرمز" if result == "red" else "سیاه"
    
    if user_choice == result:
        return {
            "result": "win",
            "amount": MULTIPLAYER_GAMES["roulette"]["base_reward"] * MULTIPLAYER_GAMES["roulette"]["win_multiplier"],
            "message": f"🎡 نتیجه: {result_text}\nبرنده‌ای! 🎉",
        }
    else:
        return {
            "result": "lose",
            "amount": -MULTIPLAYER_GAMES["roulette"]["base_reward"],
            "message": f"🎡 نتیجه: {result_text}\nبازنده! 😢",
        }

def play_card_game(user_choice):
    """بازی کارتی - کارت بالاتر"""
    player_card = random.randint(1, 13)
    bot_card = random.randint(1, 13)
    
    card_names = {1: "آس", 11: "جک", 12: "ملکه", 13: "پادشاه"}
    player_name = card_names.get(player_card, str(player_card))
    bot_name = card_names.get(bot_card, str(bot_card))
    
    if player_card > bot_card:
        return {
            "result": "win",
            "amount": MULTIPLAYER_GAMES["card_game"]["base_reward"] * MULTIPLAYER_GAMES["card_game"]["win_multiplier"],
            "message": f"🎴 شما: {player_name} | ربات: {bot_name}\nکارت شما بالاتر! 🎉",
        }
    elif player_card < bot_card:
        return {
            "result": "lose",
            "amount": -MULTIPLAYER_GAMES["card_game"]["base_reward"],
            "message": f"🎴 شما: {player_name} | ربات: {bot_name}\nکارت ربات بالاتر! 😢",
        }
    else:
        return {
            "result": "draw",
            "amount": 0,
            "message": f"🎴 برابر! {player_name}",
        }

def spin_slot_machine():
    """ماشین شانس (اسلات)"""
    symbols = ["🍎", "🍊", "🍋", "⭐", "💎", "🎰"]
    reels = [random.choice(symbols) for _ in range(3)]
    
    if reels[0] == reels[1] == reels[2]:
        # جک پات
        amount = 500
        message = f"🎰 {''.join(reels)}\n🎰 جک پات! 🎉"
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        # دو مطابقت
        amount = 150
        message = f"🎰 {''.join(reels)}\n📊 دو مطابقت! 🎊"
    else:
        # باخت
        amount = -100
        message = f"🎰 {''.join(reels)}\n😢 شانس بعدی!"
    
    return {
        "result": "win" if amount > 0 else "lose",
        "amount": amount,
        "message": message,
    }

def mini_puzzle():
    """پازل ریاضی سریع"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operation = random.choice(["+", "-", "*"])
    
    if operation == "+":
        answer = num1 + num2
        question = f"{num1} + {num2}"
    elif operation == "-":
        answer = num1 - num2
        question = f"{num1} - {num2}"
    else:
        answer = num1 * num2
        question = f"{num1} × {num2}"
    
    return {
        "question": question,
        "answer": answer,
        "base_reward": 80,
    }
