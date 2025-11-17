from flask import Flask, request, jsonify, render_template
import telebot
import random
import json
import threading

TOKEN = "8064352180:AAEK_mPLAl-S64EV1H7cWiNI2DmDr9pIZBk"
GROUP_LINK = "https://t.me/+PXHFBkzuj8liNzU0"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ----------------------
# Load/Save users
# ----------------------

def load_users():
    try:
        with open("users.json","r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json","w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)


@app.route("/")
def home():
    return render_template("access.html")


# ----------------------
# API ACCESS
# ----------------------
@app.route("/api/access", methods=["POST"])
def api_access():
    data = request.get_json()
    code = str(data.get("code","")).strip()

    users = load_users()

    # التثبت من وجود الكود
    if code not in users:
        return jsonify({"ok": False, "message": "❌ الكود غير صحيح"})

    # إذا الكود موجود → يدخل
    return jsonify({
        "ok": True,
        "message": "✔ تم التحقق",
        "invite_link": GROUP_LINK
    })


# ----------------------
# TELEGRAM BOT
# ----------------------
@bot.message_handler(commands=["start"])
def start_msg(message):
    user_id = str(message.from_user.id)
    users = load_users()

    # إنشاء كود جديد
    code = str(random.randint(100000,999999))
    users[code] = user_id
    save_users(users)

    bot.send_message(
        message.chat.id,
        f"👋 أهلا بك!\n\n🔑 هذا هو كود الدخول:\n`{code}`\n\n"
        "ادخل للرابط التالي:\nhttps://formation-digital-services-1.onrender.com/access"
        "\n\nثم ضع الكود للدخول."
    )


# ----------------------
# Run bot thread
# ----------------------
def run_bot():
    bot.infinity_polling()


threading.Thread(target=run_bot, daemon=True).start()
