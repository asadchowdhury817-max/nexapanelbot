# ==========================================
# 🚀 ULTIMATE NEXA OTP BOT v2
# ==========================================

import telebot
from telebot import types
import requests
import json
import os
import threading
import time
from datetime import datetime

# ==========================================
# ⚙️ CONFIG
# ==========================================

BOT_TOKEN = "8886260643:AAE-y8UBW69svtL16SPMN7kbpfkPSzere0Q"

API_KEY = "nxa_afd15a7eb3977a34c092ee3a91ad4a65aff13092"

BASE_URL = "http://63.141.255.227/api/v1"

OWNER_ID = 6756059606

OTP_GROUP_ID = -1003928182500

VIEW_RANGE_LINK = "https://t.me/+5157526776"

MAX_ACTIVE_ORDERS = 5

MIN_WITHDRAW = 20

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="Markdown"
)

# ==========================================
# 🔥 FAST SESSION
# ==========================================

session = requests.Session()

adapter = requests.adapters.HTTPAdapter(
    pool_connections=100,
    pool_maxsize=100
)

session.mount(
    "http://",
    adapter
)

HEADERS = {
    "X-API-KEY": API_KEY,
    "Connection": "keep-alive"
}

# ==========================================
# 💾 DATABASE
# ==========================================

DB_FILE = "database.json"

default_db = {
    "users": {},
    "banned": [],
    "active_orders": [],
    "withdraw": True,
    "withdraw_requests": [],
    "force_channels": [],
    "sent_otps": [],
    "services": {
        "facebook": {},
        "telegram": {},
        "google": {},
        "whatsapp": {},
        "instagram": {},
        "discord": {}
    }
}

# ==========================================
# 💾 LOAD DB
# ==========================================

def load_db():

    if not os.path.exists(DB_FILE):

        with open(DB_FILE, "w") as f:
            json.dump(default_db, f, indent=4)

        return default_db

    try:

        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:

        return default_db

db = load_db()

# ==========================================
# 💾 SAVE DB
# ==========================================

def save_db():

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# ==========================================
# 👤 INIT USER
# ==========================================

def init_user(user):

    uid = str(user.id)

    if uid not in db["users"]:

        ref = f"https://t.me/{bot.get_me().username}?start={uid}"

        db["users"][uid] = {

            "username": user.username,

            "balance": 0,

            "orders": 0,

            "codes": 0,

            "refers": 0,

            "history": [],

            "joined_users": [],

            "ref_link": ref,

            "last_bonus": 0,

            "last_order": 0
        }

        save_db()

# ==========================================
# 🔥 FORCE JOIN CHECK
# ==========================================

def check_join(uid):

    if not db["force_channels"]:
        return True

    for ch in db["force_channels"]:

        try:

            member = bot.get_chat_member(
                ch,
                uid
            )

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except:
            return False

    return True

# ==========================================
# 🔌 API
# ==========================================

def order_number(service, country, range_code):

    payload = {

        "service": service,

        "country": country,

        "range": range_code,

        "format": "international"
    }

    r = session.post(
        f"{BASE_URL}/numbers/get",
        json=payload,
        headers=HEADERS,
        timeout=8
    )

    return r.json()

def check_sms(number_id):

    r = session.get(
        f"{BASE_URL}/numbers/{number_id}/sms",
        headers=HEADERS,
        timeout=8
    )

    return r.json()

# ==========================================
# 🔥 OTP POLLER
# ==========================================

def otp_poller():

    while True:

        keep = []

        for order in db["active_orders"]:

            try:

                if time.time() - order["created"] > 120:
                    continue

                uid = order["uid"]

                number = order["number"]

                number_id = order["number_id"]

                range_code = order["range"]

                service = order["service"]

                country = order["country"]

                res = check_sms(number_id)

                otp = str(res.get("otp"))

                if otp and otp != "None" and otp != "null":

                    if otp in db["sent_otps"]:
                        continue

                    db["sent_otps"].append(otp)

                    msg = f"""
✅ *OTP RECEIVED*

🔥 Service:
{service}

🌍 Country:
{country}

📊 Range:
`{range_code}`

📱 Number:
`{number}`

🔑 OTP:
`{otp}`

💸 0.2৳ Added
"""

                    try:
                        bot.send_message(uid, msg)
                    except:
                        pass

                    try:
                        bot.send_message(
                            OTP_GROUP_ID,
                            msg
                        )
                    except:
                        pass

                    db["users"][str(uid)]["codes"] += 1

                    db["users"][str(uid)]["balance"] += 0.2

                    db["users"][str(uid)]["history"].append({
                        "number": number,
                        "otp": otp,
                        "time": str(datetime.now())
                    })

                    save_db()

                    continue

                keep.append(order)

            except:
                keep.append(order)

        db["active_orders"] = keep

        save_db()

        time.sleep(2)

threading.Thread(
    target=otp_poller,
    daemon=True
).start()

# ==========================================
# 📱 MAIN MENU
# ==========================================

def main_menu(uid):

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        "📱 Get Number",
        "💰 Balance"
    )

    kb.row(
        "🎁 Referral",
        "🏆 Leaderboard"
    )

    kb.row(
        "📜 History",
        "🎁 Daily Bonus"
    )

    kb.row(
        "💸 Withdraw",
        "❓ Support"
    )

    kb.row(
        "👤 Profile",
        "📢 Join Channel"
    )

    if uid == OWNER_ID:

        kb.row(
            "👑 Admin Panel"
        )

    return kb

# ==========================================
# 🚀 START
# ==========================================

@bot.message_handler(commands=["start"])
def start(m):

    uid = str(m.from_user.id)

    if uid in db["banned"]:
        return

    init_user(m.from_user)

    if not check_join(m.from_user.id):

        kb = types.InlineKeyboardMarkup()

        for ch in db["force_channels"]:

            kb.add(
                types.InlineKeyboardButton(
                    f"JOIN {ch}",
                    url=f"https://t.me/{ch.replace('@','')}"
                )
            )

        kb.add(
            types.InlineKeyboardButton(
                "✅ VERIFY",
                callback_data="verifyjoin"
            )
        )

        return bot.send_message(
            m.chat.id,
            "🚫 JOIN ALL CHANNELS",
            reply_markup=kb
        )

    args = m.text.split()

    if len(args) > 1:

        ref = args[1]

        if (
            ref != uid
            and ref in db["users"]
            and uid not in db["users"][ref]["joined_users"]
        ):

            db["users"][ref]["balance"] += 2

            db["users"][ref]["refers"] += 1

            db["users"][ref]["joined_users"].append(uid)

            save_db()

    bot.send_message(
        m.chat.id,
        "🔥 WELCOME TO NEXA OTP BOT",
        reply_markup=main_menu(m.from_user.id)
    )

# ==========================================
# ✅ VERIFY JOIN
# ==========================================

@bot.callback_query_handler(
    func=lambda c:
    c.data == "verifyjoin"
)
def verifyjoin(c):

    if check_join(c.from_user.id):

        bot.send_message(
            c.message.chat.id,
            "✅ VERIFIED",
            reply_markup=main_menu(c.from_user.id)
        )

    else:

        bot.answer_callback_query(
            c.id,
            "❌ JOIN ALL CHANNELS"
        )

# ==========================================
# 📱 GET NUMBER
# ==========================================

@bot.message_handler(
    func=lambda m:
    m.text == "📱 Get Number"
)
def get_number(m):

    uid = str(m.from_user.id)

    if time.time() - db["users"][uid]["last_order"] < 3:

        return bot.send_message(
            m.chat.id,
            "⚠️ WAIT 3 SECONDS"
        )

    active = 0

    for x in db["active_orders"]:

        if str(x["uid"]) == uid:
            active += 1

    if active >= MAX_ACTIVE_ORDERS:

        return bot.send_message(
            m.chat.id,
            f"❌ MAX {MAX_ACTIVE_ORDERS} ACTIVE ORDERS"
        )

    msg = bot.send_message(
        m.chat.id,
        """
⬆️ ENTER RANGE ID

Example:
22898XXX
"""
    )

    bot.register_next_step_handler(
        msg,
        process_range
    )

# ==========================================
# 🔥 PROCESS RANGE
# ==========================================

def process_range(m):

    uid = str(m.from_user.id)

    range_code = m.text.strip()

    db["users"][uid]["last_order"] = time.time()

    save_db()

    service = "facebook"

    country = "Togo 🇹🇬"

    try:

        res = order_number(
            service,
            country,
            range_code
        )

        if not res.get("success"):

            return bot.send_message(
                m.chat.id,
                f"❌ {res.get('message')}"
            )

        number = res.get("number")

        number_id = res.get("number_id")

        db["active_orders"].append({

            "uid": m.from_user.id,

            "number": number,

            "number_id": number_id,

            "range": range_code,

            "service": service,

            "country": country,

            "created": time.time()
        })

        db["users"][uid]["orders"] += 1

        save_db()

        text = f"""
🎉 *YOUR NUMBER ADDED 👀*

📊 Range:
`{range_code}`

🌍 Country:
{country}

📞 Number:
`{number}`

📩 SMS Status:
`Waiting...`
"""

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "🔥 Change Number",
                callback_data=f"change_{range_code}"
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                "📊 View Range",
                url=VIEW_RANGE_LINK
            )
        )

        bot.send_message(
            m.chat.id,
            text,
            reply_markup=kb
        )

    except Exception as e:

        bot.send_message(
            m.chat.id,
            f"❌ Error:\n{e}"
        )

# ==========================================
# 🔄 CHANGE NUMBER
# ==========================================

@bot.callback_query_handler(
    func=lambda c:
    c.data.startswith("change_")
)
def change(c):

    range_code = c.data.split("_")[1]

    service = "facebook"

    country = "Togo 🇹🇬"

    try:

        res = order_number(
            service,
            country,
            range_code
        )

        if not res.get("success"):

            return bot.answer_callback_query(
                c.id,
                "❌ NO STOCK"
            )

        number = res.get("number")

        number_id = res.get("number_id")

        db["active_orders"].append({

            "uid": c.from_user.id,

            "number": number,

            "number_id": number_id,

            "range": range_code,

            "service": service,

            "country": country,

            "created": time.time()
        })

        save_db()

        text = f"""
🎉 *YOUR NUMBER CHANGED 👀*

📊 Range:
`{range_code}`

🌍 Country:
{country}

📞 Number:
`{number}`

📩 SMS Status:
`Waiting...`
"""

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "🔥 Change Number",
                callback_data=f"change_{range_code}"
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                "📊 View Range",
                url=VIEW_RANGE_LINK
            )
        )

        bot.edit_message_text(
            text,
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb
        )

    except Exception as e:

        bot.answer_callback_query(
            c.id,
            str(e)
        )

# ==========================================
# 💰 BALANCE
# ==========================================

@bot.message_handler(
    func=lambda m:
    m.text == "💰 Balance"
)
def balance(m):

    bal = db["users"][str(m.from_user.id)]["balance"]

    bot.send_message(
        m.chat.id,
        f"💰 YOUR BALANCE\n\n৳ {bal}"
    )

# ==========================================
# 🏆 LEADERBOARD
# ==========================================

@bot.message_handler(
    func=lambda m:
    m.text == "🏆 Leaderboard"
)
def leaderboard(m):

    users = sorted(
        db["users"].items(),
        key=lambda x: x[1]["codes"],
        reverse=True
    )

    text = "🏆 TOP OTP USERS\n\n"

    pos = 1

    for uid, user in users[:10]:

        text += f"""
{pos}. `{uid}`
📩 OTP: {user['codes']}
💰 ৳{user['balance']}

"""

        pos += 1

    bot.send_message(
        m.chat.id,
        text
    )

# ==========================================
# 🎁 DAILY BONUS
# ==========================================

@bot.message_handler(
    func=lambda m:
    m.text == "🎁 Daily Bonus"
)
def daily_bonus(m):

    uid = str(m.from_user.id)

    now = time.time()

    last = db["users"][uid]["last_bonus"]

    if now - last < 86400:

        return bot.send_message(
            m.chat.id,
            "❌ BONUS ALREADY CLAIMED"
        )

    db["users"][uid]["balance"] += 1

    db["users"][uid]["last_bonus"] = now

    save_db()

    bot.send_message(
        m.chat.id,
        "🎁 1৳ BONUS ADDED"
    )

# ==========================================
# 📜 HISTORY
# ==========================================

@bot.message_handler(
    func=lambda m:
    m.text == "📜 History"
)
def history(m):

    uid = str(m.from_user.id)

    hist = db["users"][uid]["history"]

    if not hist:

        return bot.send_message(
            m.chat.id,
            "❌ NO HISTORY"
        )

    text = "📜 LAST HISTORY\n\n"

    for x in hist[-10:]:

        text += f"""
📱 {x['number']}
🔑 {x['otp']}
⏰ {x['time']}

"""

    bot.send_message(
        m.chat.id,
        text
    )
