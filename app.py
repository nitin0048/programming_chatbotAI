from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
import datetime
import requests
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "aura_chatbot_secret"  # Secret key for session management


# ===============================
# Database Connection Helper
# ===============================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="programming_bot"
    )


# ===============================
# Fetch answer from QA bank
# ===============================
def fetch_answer(question):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        query = "SELECT answer FROM qa_bank WHERE question LIKE %s"
        cursor.execute(query, ("%" + question + "%",))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None


# ==================================
# Arithmetic / Relational / Logical
# ==================================
def calculate_expression(question):
    q = question.lower()

    # 1️⃣ Convert number words to digits
    word_to_num = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
        "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
        "eighty": "80", "ninety": "90", "hundred": "100"
    }
    for word, num in word_to_num.items():
        q = q.replace(word, num)

    # 2️⃣ Convert operator words
    replacements = {
        "plus": "+", "add": "+", "added to": "+",
        "minus": "-", "subtract": "-", "subtracted from": "-",
        "multiply": "*", "multiplied by": "*", "times": "*", "into": "*", "x": "*",
        "divide": "/", "divided by": "/",
        "mod": "%", "remainder": "%", "modulus": "%",
        "power": "**", "raised to": "**",
        "greater than": ">", "less than": "<",
        "equal to": "==", "equals": "==",
        "not equal to": "!="
    }
    for word, symbol in replacements.items():
        q = q.replace(word, symbol)

    q = q.replace(" ", "")

    # 3️⃣ Try arithmetic
    try:
        if any(op in q for op in ["+", "-", "*", "/", "%", "**"]):
            result = eval(q)
            return f"✅ Answer: {result}"
    except:
        pass

    # 4️⃣ Relational
    try:
        if any(op in q for op in [">", "<", ">=", "<=", "==", "!="]):
            result = eval(q)
            return f"✅ Result: {result}"
    except:
        pass

    # 5️⃣ Logical
    if "and" in q or "or" in q or "not" in q:
        logical_q = q.replace("true", "True").replace("false", "False")
        try:
            result = eval(logical_q)
            return f"✅ Logical Result: {result}"
        except:
            pass

    return None


# ===============================
# Basic responses (built-in)
# ===============================
def get_basic_response(question):
    q = question.lower()
    now = datetime.datetime.now()

    if "hello" in q or "hi" in q or "hey" in q:
        return "👋 Hello! I am Aura — your programming chatbot AI!"
    elif "how are you" in q:
        return "🤖 I'm functioning perfectly! Thanks for asking 😄"
    elif "what are you doing" in q:
        return "🤖 I'm chatting with you and learning new things! 💬"
    elif "who made you" in q:
        return "🤖 You made me, of course! 💡"
    elif "your name" in q:
        return "🤖 My name is Aura — your friendly assistant! ✨"
    elif "help me" in q:
        return "🤖 I can help you with programming concepts, logic, and more!"
    elif "thank" in q:
        return "🤖 You're welcome! 😊"
    elif "my name" in q:
        return "🤖 Yes! Your name is Nitin Gunjavate 😄"

    # Date & Time
    if "time" in q:
        return f"⏰ Current Time: {now.strftime('%I:%M %p')}"
    if "date" in q:
        return f"📅 Today's Date: {now.strftime('%B %d, %Y')}"
    if "day" in q:
        return f"🗓 Today is {now.strftime('%A')}"
    if "month" in q:
        return f"📅 Current Month: {now.strftime('%B')}"
    if "year" in q:
        return f"📅 Current Year: {now.year}"

    # Part of the day
    hour = now.hour
    if "morning" in q or "afternoon" in q or "evening" in q or "night" in q or "part of day" in q:
        if 5 <= hour < 12:
            return "🌄 It's Morning."
        elif 12 <= hour < 16:
            return "☀️ It's Afternoon."
        elif 16 <= hour < 20:
            return "🌆 It's Evening."
        else:
            return "🌙 It's Night."

    # Leap year
    if "leap year" in q:
        year = now.year
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return f"✅ Yes, {year} is a leap year."
        else:
            return f"❌ No, {year} is not a leap year."

    # Weather
    if "weather" in q:
        city = "Mumbai"
        try:
            response = requests.get(f"https://wttr.in/{city}?format=3")
            return f"🌦 {response.text}"
        except:
            return "⚠ Unable to fetch weather right now."

    return None


# ===============================
# ROUTES: Login, Register, Logout
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["username"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password!")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
            return redirect(url_for("login"))
        except:
            return render_template("register.html", error="Username already exists!")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# ===============================
# Chatbot Main Page (Protected)
# ===============================
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])


# ===============================
# Chatbot Q&A Endpoint
# ===============================
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")

    # Check built-in responses
    basic = get_basic_response(question)
    if basic:
        return jsonify({"answer": basic})

    # Try calculations
    calc = calculate_expression(question)
    if calc:
        return jsonify({"answer": calc})

    # Fetch from DB
    db_answer = fetch_answer(question)
    if db_answer:
        return jsonify({"answer": f"🤖 {db_answer}"})

    return jsonify({"answer": "🤖 Sorry, I don't know that yet."})


if __name__ == "__main__":
    app.run(debug=True)
