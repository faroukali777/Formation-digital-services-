from flask import Flask, render_template, request
import json
import threading
import telebot

# ===== إعدادات البوت =====
TOKEN = "8064352180:AAGEzj6mROn7sBl5r8lRPAxwtP5V_zIFzrA"
bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.json"

# ===== دوال حفظ / قراءة الأكواد =====
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except:
        return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# ===== منطق البوت على تيليغرام =====

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🎉 مرحبا! أرسل الكود اللي تحب تعطيه للكلون، "
        "وهو يدخل بيه في الموقع.\n\n"
        "مثال: 123456"
    )

@bot.message_handler(func=lambda m: True)
def add_code(message):
    code = message.text.strip()

    # نمنعو الأكواد الفارغة أو القصيرة برشا
    if len(code) < 3:
        bot.reply_to(message, "❌ الكود قصير برشا. جرّب كود أطول شوية.")
        return

    users = load_users()
    users[code] = True         # نخزّن الكود كصالح
    save_users(users)

    bot.reply_to(
        message,
        f"✔️ تم إضافة الكود `{code}` بنجاح!\n"
        "قلّه يمشي للموقع ويحط نفس الكود باش يدخل للكورس. 😉",
        parse_mode="Markdown"
    )


# ===== تطبيق الويب (Flask) =====

app = Flask(__name__)

@app.route("/")
def home():
    # صفحة الدخول
    return render_template("access.html")

@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        users = load_users()

        if users.get(code):
            return "✔️ تم التحقق — مرحبا بك في الكورس 🎓"
        else:
            return "❌ الكود غير صحيح، تواصل مع الدعم."

    # GET → يرجّع الفورم
    return render_template("access.html")


# ===== تشغيل البوت في Thread =====

def run_bot():
    bot.infinity_polling(skip_pending=True)

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
