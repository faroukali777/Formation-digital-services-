from flask import Flask, request, jsonify, render_template
import json, os, hashlib, random, threading
import telebot

# ========= الإعدادات =========
BOT_TOKEN  = "8064352180:AAEK_mPLAl-S64EV1H7cWiNI2DmDr9pIZBk"

USERS_FILE = "users.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# ================= JSON HELPERS ===============
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
            "otp": None,
            "otp_required": False,
            "otp_attempts": 0
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

# ================= FINGERPRINT =================
def make_fingerprint(req):
    ip   = req.headers.get("X-Forwarded-For", req.remote_addr) or "0"
    ua   = req.headers.get("User-Agent", "ua")
    lang = req.headers.get("Accept-Language", "lang")
    raw  = f"{ip}|{ua}|{lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

# ============ Telegram Bot ==============

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    data = get_user(user_id)

    if not data.get("code"):
        code = str(random.randint(100000, 999999))
        update_user(user_id, {"code": code})
    else:
        code = data["code"]

    site_url = "https://formation-digital-services-1.onrender.com/access"

    txt = (
        "👋 أهلاً بيك في *Formation Digital Services*\n\n"
        "🔐 هذا الكود الخاص بيك:\n"
        f"`{code}`\n\n"
        "أدخل للرابط هذا باش تعمل التحقق:\n"
        f"{site_url}"
    )

    bot.reply_to(message, txt)

# =============== WEB ROUTES ==================

@app.route("/")
def home():
    return render_template("access.html")

@app.route("/access")
def access_page():
    return render_template("access.html")

# =============== /api/access ==================

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

    if not user_id:
        return jsonify({"ok": False, "message": "❌ الكود غير موجود."})

    current_fp = make_fingerprint(request)

    # أول جهاز
    if not user_info.get("fingerprint"):
        update_user(user_id, {
            "fingerprint": current_fp,
            "verified": True
        })
        return jsonify({
            "ok": True,
            "message": "🚀 تم تأكيد الجهاز — ادخل للقروب الجديد",
            "invite_link": "https://t.me/+r8Ikjh_5EfhjZjA0"
        })

    # نفس الجهاز
    if user_info.get("fingerprint") == current_fp:
        return jsonify({
            "ok": True,
            "message": "🚀 مرحبا بيك — جهازك معروف",
            "invite_link": "https://t.me/+r8Ikjh_5EfhjZjA0"
        })

    # جهاز جديد → OTP
    otp = generate_otp()
    update_user(user_id, {
        "otp": otp,
        "otp_required": True,
        "otp_attempts": 0
    })

    bot.send_message(
        user_id,
        f"⚠️ محاولة دخول من جهاز جديد.\nOTP متاعك:\n`{otp}`"
    )

    return jsonify({
        "ok": False,
        "need_otp": True,
        "message": "🔐 دخل الـ OTP المبعوث في البوت."
    })

# =============== VERIFY OTP ==================

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

    if otp_input != user_info.get("otp"):
        return jsonify({"ok": False, "message": "❌ OTP غلط."})

    update_user(user_id, {
        "fingerprint": make_fingerprint(request),
        "verified": True,
        "otp": None,
        "otp_required": False
    })

    return jsonify({
        "ok": True,
        "message": "🎉 جهازك الجديد مقبول",
        "invite_link": "https://t.me/+r8Ikjh_5EfhjZjA0"
    })

# ========= BOT THREAD =========

def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot, daemon=True).start()
