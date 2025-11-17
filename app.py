from flask import Flask, request, jsonify, render_template
import json, os, hashlib, random, threading
import telebot

# ========= الإعدادات =========
BOT_TOKEN  = "8064352180:AAGEzj6mROn7sBl5r8lRPAxwtP5V_zIFzrA"
CHANNEL_ID = -1002675184687
ADMIN_ID   = 6731717152

USERS_FILE = "users.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__, template_folder="templates")


# ========= Helpers: JSON =========
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: int):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "code": None,
            "fingerprint": None,
            "verified": False,
            "invite_link": None,
            "banned": False,
            "otp": None,
            "otp_attempts": 0,
            "otp_required": False
        }
        save_users(users)
    return users[uid]


def update_user(user_id: int, new_data: dict):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {}
    users[uid].update(new_data)
    save_users(users)


# ========= Fingerprint + OTP =========
def make_fingerprint(req):
    ip   = req.headers.get("X-Forwarded-For", req.remote_addr) or "0"
    ua   = req.headers.get("User-Agent", "ua")
    lang = req.headers.get("Accept-Language", "lang")
    raw  = f"{ip}|{ua}|{lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))


# ========= رابط دعوة =========
def create_one_time_link():
    invite = bot.create_chat_invite_link(
        CHANNEL_ID,
        member_limit=1
    )
    return invite.invite_link


# ========= Telegram /start =========

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    data = get_user(user_id)

    if data.get("banned"):
        bot.reply_to(message, "⛔ أنت محظور.")
        return

    if not data.get("code"):
        code = str(random.randint(100000, 999999))
        update_user(user_id, {"code": code})
    else:
        code = data["code"]

    site_url = "https://formation-digital-services-1.onrender.com/access"

    txt = (
        "👋 أهلاً بيك في *Formation digital services*\n\n"
        "🔐 *كود الدخول الخاص بيك:*\n"
        f"`{code}`\n\n"
        "✅ إدخل للموقع وحط الكود.\n\n"
        f"🌐 رابط الموقع:\n{site_url}"
    )
    bot.reply_to(message, txt)


# ========= Web Pages =========

@app.route("/")
def home():
    return render_template("access.html")

@app.route("/access")
def access_page():
    return render_template("access.html")


# ========= API: Step 1 =========

@app.route("/api/access", methods=["POST"])
def api_access():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    if not code.isdigit():
        return jsonify({"ok": False, "message": "❌ الكود غير صالح."})

    users = load_users()
    user_id = None
    user_info = None

    for uid, info in users.items():
        if str(info.get("code")) == code:
            user_id = int(uid)
            user_info = info
            break

    if user_id is None:
        return jsonify({"ok": False, "message": "❌ الكود غير موجود."})

    if user_info.get("banned"):
        return jsonify({"ok": False, "message": "⛔ أنت محظور."})

    current_fp = make_fingerprint(request)

    if not user_info.get("fingerprint"):
        user_info["fingerprint"] = current_fp
        user_info["verified"] = True
        user_info["otp"] = None
        user_info["otp_attempts"] = 0
        user_info["otp_required"] = False
        users[str(user_id)] = user_info
        save_users(users)

        try:
            invite_link = create_one_time_link()
            user_info["invite_link"] = invite_link
            save_users(users)
            return jsonify({
                "ok": True,
                "message": "✅ جهازك تربط.",
                "invite_link": invite_link
            })
        except:
            return jsonify({"ok": False, "message": "⚠ خطأ في إنشاء الرابط."})

    if user_info.get("fingerprint") == current_fp and user_info.get("verified"):
        try:
            invite_link = create_one_time_link()
            user_info["invite_link"] = invite_link
            save_users(users)
            return jsonify({
                "ok": True,
                "message": "✅ مرحبا بيك.",
                "invite_link": invite_link
            })
        except:
            return jsonify({"ok": False, "message": "⚠ خطأ في إنشاء الرابط."})

    otp = generate_otp()
    user_info["otp"] = otp
    user_info["otp_attempts"] = 0
    user_info["otp_required"] = True
    save_users(users)

    try:
        bot.send_message(user_id, f"🔐 *OTP*: `{otp}`")
        bot.send_message(ADMIN_ID, f"⚠ جهاز جديد للمستخدم {user_id}")
    except:
        pass

    return jsonify({
        "ok": False,
        "need_otp": True,
        "message": "⚠ جهاز جديد، تم إرسال OTP."
    })


# ========= API: Verify OTP =========

@app.route("/api/verify-otp", methods=["POST"])
def api_verify_otp():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    otp_input = (data.get("otp") or "").strip()

    users = load_users()
    user_id = None
    user_info = None

    for uid, info in users.items():
        if str(info.get("code")) == code:
            user_id = int(uid)
            user_info = info
            break

    if otp_input != str(user_info.get("otp")):
        return jsonify({"ok": False, "message": "❌ OTP غلط."})

    current_fp = make_fingerprint(request)
    user_info["fingerprint"] = current_fp
    user_info["verified"] = True
    user_info["otp"] = None
    user_info["otp_required"] = False
    save_users(users)

    invite_link = create_one_time_link()
    return jsonify({
        "ok": True,
        "message": "✅ جهازك مقبول.",
        "invite_link": invite_link
    })


# ========= Run Bot Thread =========
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot, daemon=True).start()
