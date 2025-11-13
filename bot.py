import telebot
from telebot import types

BOT_TOKEN = "8064352180:AAEDY8JnnpY42ryiSOMYwHzHSTHDsbhdecg"
ADMIN_ID = 6731717152
CHANNEL_ID = -1002675184687

bot = telebot.TeleBot(BOT_TOKEN)

users_devices = {}

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    if not is_member(user_id):
        bot.send_message(user_id, "❌ يلزمك تدخل للقناة قبل:\nhttps://t.me/+N1HQ3bDpCMs1Mjc0")
        return

    device_id = msg.chat.id

    if user_id not in users_devices:
        users_devices[user_id] = device_id
        bot.send_message(user_id, "✅ تم تسجيل جهازك كجهاز أساسي.")
    else:
        if users_devices[user_id] != device_id:
            bot.send_message(user_id, "❌ تم اكتشاف دخول من جهاز آخر! يتم طردك من القناة...")
            try:
                bot.ban_chat_member(CHANNEL_ID, user_id)
            except:
                bot.send_message(ADMIN_ID, "⚠️ ما نجمتش نطرد الشخص، يلزم صلاحيات أكبر.")
        else:
            bot.send_message(user_id, "✔️ إنت متصل من جهازك العادي.")

bot.infinity_polling()
