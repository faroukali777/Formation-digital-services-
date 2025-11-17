from flask import Flask, request, jsonify, render_template
import json, os, hashlib, random, threading
import telebot

# ========= الإعدادات =========
BOT_TOKEN  = "8064352180:AAEK_mPLAl-S64EV1H7cWiNI2DmDr9pIZBk"   # التوكن الجديد
CHANNEL_ID = -1003487080023   # السوبر قروب الجديد لي جبناه
ADMIN_ID   = 6731717152

USERS_FILE = "users.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

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

def get_user(uid):
    users = load_users()
    uid = str(uid)
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

def update_user(user_id, new_data):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {}
    users[uid].update(new_data)
    save_users(users)

# ========= Fingerprint =========
def make_fingerprint(req):
    ip   = req.headers.get("X-Forwarded-For", req.remote_addr) or "0"
    ua   = req.headers.get("User-Agent", "ua")
    lang = req.headers.get("Accept-Language", "lang")
    raw  = f"{ip}|{ua}|{lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

# ========= إنشاء رابط واحد =========
def create_one_time_link():
    invite = bot.create_chat_invite_link(
        CHAT_ID := CHANNEL_ID,
        member_limit=1
    )
    return invite.invite_link

# ========= Telegram Bot =========
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
        "👋 أهلاً بيك\n\n"
        "🔐 *كود الدخول:*\n"
        f"`{code}`\n\n"
        "🌐 رابط الموقع:\n"
        f"{site_url}"
    )
    bot.reply_to(message, txt)

# ========= Flask =========
@app.route("/")
def home():
    return render_template("access.html")

@app.route("/access")
def access_page():
    return render_template("access.html")

@app.route("/api/access", methods=["POST"])
def api_access():
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()

    if not code.isdigit():
        return jsonify({"ok": False, "message": "❌ الكود غير صحيح."})

    users = load_users()
    user_id = None
    user_info = None

    for uid, info in users.items():
        if str(info.get("code")) == code:
            user_id = int(uid)
            user_info = info
            break

    if not user_id:
        return jsonify({"ok": False, "message": "❌ الكود هذا غير موجود."})

    if user_info.get("banned"):
        return jsonify({"ok": False, "message": "⛔ أنت محظور."})

    fp = make_fingerprint(request)

    # أول جهاز
    if not user_info.get("fingerprint"):
        user_info["fingerprint"] = fp
        user_info["verified"] = True
        user_info["otp"] = None
        user_info["otp_required"] = False
        save_users(users)

        link = create_one_time_link()
        user_info["invite_link"] = link
        save_users(users)

        return jsonify({"ok": True, "invite_link": link})

    # نفس الجهاز
    if user_info.get("fingerprint") == fp:
        link = create_one_time_link()
        user_info["invite_link"] = link
        save_users(users)
        return jsonify({"ok": True, "invite_link": link})

    # جهاز جديد → OTP
    otp = generate_otp()
    user_info["otp"] = otp
    user_info["otp_required"] = True
    user_info["otp_attempts"] = 0
    save_users(users)

    bot.send_message(user_id, f"🔐 كود التحقق:\n`{otp}`")
    bot.send_message(ADMIN_ID, f"⚠️ جهاز جديد للمستخدم {user_id}")

    return jsonify({"ok": False, "need_otp": True, "message": "🔐 أدخل OTP."})

@app.route("/api/verify-otp", methods=["POST"])
def api_verify_otp():
    data = request.get_json() or {}
    code = data.get("code","").strip()
    otp_in = data.get("otp","").strip()

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

    if otp_in != str(user_info.get("otp")):
        return jsonify({"ok": False, "message": "❌ OTP خاطئ."})

    fp = make_fingerprint(request)

    user_info["fingerprint"] = fp
    user_info["verified"] = True
    user_info["otp"] = None
    user_info["otp_required"] = False
    save_users(users)

    link = create_one_time_link()
    user_info["invite_link"] = link
    save_users(users)

    return jsonify({"ok": True, "invite_link": link})

# ========= تشغيل البوت داخل Render =========
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot, daemon=True).start()
