import telebot
import json

TOKEN = "8064352180:AAGEzj6mROn7sBl5r8lRPAxwtP5V_zIFzrA"
bot = telebot.TeleBot(TOKEN)

# Load users
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

# Save users
def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎉 مرحبا! أعطيني الكود باش نفعّلك الدخول.")

@bot.message_handler(func=lambda m: True)
def check_code(message):
    code = message.text.strip()
    users = load_users()
    users[code] = True
    save_users(users)

    bot.reply_to(message, "✔️ تم إضافة الكود بنجاح!")

bot.infinity_polling()
