from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)

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

@app.route("/")
def home():
    return redirect("/access")

@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form.get("code")
        users = load_users()

        if code in users:
            return "✔️ تم التحقق — مرحبا بك في الكورس"
        else:
            return "❌ الكود غير صحيح"

    return render_template("access.html")

if __name__ == "__main__":
    app.run()
