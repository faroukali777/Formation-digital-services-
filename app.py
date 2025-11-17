from flask import Flask, request, jsonify, render_template
import json, os, hashlib, random
import telebot

# ========= الإعدادات =========
BOT_TOKEN  = "8064352180:AAFuU1smfmIkLq3xA6Eb1A3MdBT1n5_SpLw"
CHANNEL_ID = -1002675184687
ADMIN_ID   = 6731717152

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
USERS_FILE = "users.json"

app = Flask(__name__)


# ========= JSON Helpers =========
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ========= Fingerprint =========
def make_fp(req):
    ip   = req.headers.get("X-Forwarded-For", req.remote_addr) or "0"
    ua   = req.headers.get("User-Agent", "ua")
    base = f"{ip}|{ua}"
    return hashlib.sha256(base.encode()).hexdigest()


# ========= ROUTES =========
@app.route("/")
def home():
    return render_template("access.html")


# ====== API: التحقق بالكود + الجهاز ======
@app.route("/api/access", methods=["POST"])
def api_access():
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()

    if not code:
        return jsonify({"ok": False, "message": "❌ أدخل كود صحيح"})

    users = load_users()

    user_id = None
    user = None

    # نلقى المستخدم بالكود
    for uid, info in users.items():
        if str(info.get("code")) == code:
            user_id = uid
            user = info
            break

    if user is None:
        return jsonify({"ok": False, "message": "❌ الكود غير موجود"})

    # fingerprint الحالي
    fp_now = make_fp(request)

    # أول مرة
    if not user.get("verified"):
        user["verified"] = True
        user["fingerprint"] = fp_now
        save_users(users)

        try:
            invite = bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
            return jsonify({"ok": True, "invite_link": invite.invite_link})
        except:
            return jsonify({"ok": False, "message": "⚠️ مشكل في إنشاء الرابط"})

    # جهاز مختلف؟
    if user.get("fingerprint") != fp_now:
        return jsonify({"ok": False, "message": "❌ دخول مرفوض: جهاز جديد"})

    # جهاز صحيح → نرجّع رابط جديد
    try:
        invite = bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        return jsonify({"ok": True, "invite_link": invite.invite_link})
    except:
        return jsonify({"ok": False, "message": "⚠️ مشكلة في الرابط"})


# ============= Run =============
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
