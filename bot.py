import telebot
import json
import os

BOT_TOKEN = "8064352180:AAFuU1smfmIkLq3xA6Eb1A3MdBT1n5_SpLw"
USERS_FILE = "users.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")


# تحميل المستخدمين
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except:
        return {}


# حفظ المستخدمين
def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@bot.message_handler(commands=["start"])
def send_code(message):
    user_id = str(message.chat.id)

    users = load_users()

    # إذا المستخدم موش مسجل → نسجّل كود جديد
    if user_id not in users or "code" not in users[user_id]:
        generated_code = str(message.chat.id)[-6:]  # كود ثابت للمستخدم = آخر 6 أرقام
        users[user_id] = {
            "code": generated_code,
            "verified": False,
            "fingerprint": None
        }
        save_users(users)
    else:
        generated_code = users[user_id]["code"]

    bot.reply_to(
        message,
        f"🔐 *كود الدخول متاعك:*\n`{generated_code}`\n\n"
        "⬅️ أمشي للموقع وأدخل الكود.\n"
    )


bot.infinity_polling()
