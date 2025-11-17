from flask import Flask, request, jsonify, render_template, redirect
import json
import os
import random
import telebot
from telebot.types import Update

# ===== إعداداتك =====
BOT_TOKEN   = "8064352180:AAEK_mPLAl-S64EV1H7cWiNI2DmDr9pIZBk"  # التوكن متاع البوت
GROUP_LINK  = "https://t.me/+r8Ikjh_5EfhjZjA0"  # رابط السوبر قروب متاع الفورمسيون
USERS_FILE  = "users.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)


# ===== helpers متاع الكودات =====
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except:
        return {}


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_code(users_dict):
    """يولّد كود 6 أرقام وما يتعاودش"""
    while True:
        code = str(random.randint(100000, 999999))
        if code not in users_dict:
            return code


# ===== بوت تيليجرام =====
@bot.message_handler(commands=['start'])
def handle_start(message):
    users = load_users()

    # نولّد كود جديد لكل start (ينجم يكون عندو برشا أكواد ما يضرش)
    code = generate_code(users)
    users[code] = {
        "user_id": message.from_user.id
    }
    save_users(users)

    site_url = "https://formation-digital-services-1.onrender.com/access"

    txt = (
        "👋 أهلاً بيك في *Formation digital services*\n\n"
        "🔐 هذا *كود الدخول* الخاص بيك:\n"
        f"`{code}`\n\n"
        "✅ إدخل للموقع وحط الكود باش يفتحلك الفورمسيون.\n\n"
        f"🌐 رابط الموقع:\n{site_url}"
    )
    bot.reply_to(message, txt)


# ===== Flask Routes =====

@app.route("/")
def home():
    # نخلي / يحوّل مباشرة لـ /access
    return redirect("/access")


@app.route("/access")
def access_page():
    # هذا يستعمل access.html اللي عندك
    return render_template("access.html")


@app.route("/api/access", methods=["POST"])
def api_access():
    """الموقع يتحقّق من الكود ويرجع رابط القروب إذا صحيح"""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    if not code:
        return jsonify({"ok": False, "message": "❌ أدخل الكود."})

    users = load_users()

    if code in users:
        # هنا ينجم الكود يكون One-Time لو تحب:
        # del users[code]; save_users(users)
        return jsonify({
            "ok": True,
            "message": "✅ تم التحقق! سيتم تحويلك للسوبر قروب.",
            "invite_link": GROUP_LINK
        })
    else:
        return jsonify({"ok": False, "message": "❌ الكود غير صحيح."})


# ===== Webhook متاع البوت =====

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    """تيليجرام يبعث التحديثات (messages) لهنا"""
    json_str = request.get_data().decode("utf-8")
    update = Update.de_json(json.loads(json_str))
    bot.process_new_updates([update])
    return "OK", 200


if __name__ == "__main__":
    # لو تشغّلها محلياً
    app.run(host="0.0.0.0", port=5000, debug=True)
