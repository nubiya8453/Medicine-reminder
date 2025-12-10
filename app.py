# app.py — complete, robust version with automatic daily medicine reminders
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import logging
import os
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import re
import os




# -------------------------
# Import recommender
# -------------------------
from recommender import Recommender

# -------------------------
# Flask + Logging setup
# -------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET", "supersecretkey")
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medicine_app")

# -------------------------
# MongoDB setup
# -------------------------
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/medicine_reminder")
try:
    mongo = PyMongo(app)
    users_col = mongo.db.users
    patients_col = mongo.db.patients
    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.exception("❌ Could not connect to MongoDB: %s", e)
    mongo = None
    users_col = None
    patients_col = None

# -------------------------
# Load recommender model
# -------------------------
try:
    recommender = Recommender("disease_medicine_schedule.xlsx")
except Exception as e:
    logger.exception("⚠️ Failed to initialize recommender: %s", e)
    recommender = None

# -------------------------
# Gmail credentials
# -------------------------
SENDER_EMAIL = "nubiyafathima0@gmail.com"
SENDER_PASSWORD = "wdnv typb geib rmfy"  # Gmail App Password

# -------------------------
# Helper to get data from request
# -------------------------
def get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    try:
        data = get_request_data()
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        logger.info("📩 Register attempt — username: %s email: %s", username, email)

        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        if users_col is None:
            return jsonify({"error": "Database not connected"}), 500

        existing = users_col.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing:
            return jsonify({"error": "Username or email already exists"}), 400

        hashed = generate_password_hash(password)
        users_col.insert_one({
            "username": username,
            "email": email,
            "password": hashed
        })
        logger.info("✅ Registered user %s", username)
        return jsonify({"success": True, "redirect": "/dashboard"})
    except Exception as e:
        logger.exception("❌ Error in /register: %s", e)
        return jsonify({"error": "Server error during registration"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = get_request_data()
        username_or_email = (data.get("username") or "").strip()
        password = data.get("password") or ""

        logger.info("🔐 Login attempt: %s", username_or_email)

        if not username_or_email or not password:
            return jsonify({"error": "Username/email and password required"}), 400

        if users_col is None:
            return jsonify({"error": "Database not connected"}), 500

        user = users_col.find_one({
            "$or": [
                {"username": {"$regex": f"^{username_or_email}$", "$options": "i"}},
                {"email": {"$regex": f"^{username_or_email}$", "$options": "i"}}
            ]
        })

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Incorrect password"}), 401

        session["username"] = user["username"]
        logger.info("✅ Login successful for: %s", user["username"])
        return jsonify({"success": True, "redirect": "/dashboard"})
    except Exception as e:
        logger.exception("❌ Error in /login: %s", e)
        return jsonify({"error": "Server error during login"}), 500

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html", username=session["username"])

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json(force=True)
        patient_name = data.get("patient_name")
        age = data.get("age")
        gender = data.get("gender")
        email = data.get("email")
        disease = (data.get("disease") or "").strip()

        rec = recommender.recommend(disease)
        patients_col.insert_one({
            "patient_name": patient_name,
            "age": age,
            "gender": gender,
            "email": email,
            "disease": rec.get("disease"),
            "medicine": rec.get("medicine"),
            "dosage": rec.get("dosage"),
            "time_to_take": rec.get("time_to_take")
        })

        subject = f"💊 Medicine Recommendation for {rec['disease']}"
        body = f"""
Hello {patient_name},

Based on your health condition ({rec['disease']}), here is your recommended medication:

💊 Medicine: {rec['medicine']}
💧 Dosage: {rec['dosage']}
⏰ Timing: {rec['time_to_take']}

Please follow this schedule and consult your doctor if you experience any issues.

Stay healthy and take care 💙
— Medicine Reminder System
"""

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print(f"✅ Recommendation email sent successfully to {email}")

        return jsonify({
            "success": True,
            "medicine": rec.get("medicine", "N/A"),
            "dosage": rec.get("dosage", "N/A"),
            "timing": rec.get("time_to_take", "N/A")
        })
    except Exception as e:
        print("❌ Error in /recommend:", e)
        return jsonify({"success": False, "error": "Failed to generate recommendation"}), 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ======================
# Forgot Password Routes
# ======================
serializer = URLSafeTimedSerializer(app.secret_key)

def send_email(to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "Email not found."})

    token = serializer.dumps(email, salt="password-reset-salt")
    reset_link = f"http://127.0.0.1:5000/reset-password?token={token}"

    send_email(
        email,
        "🔑 Password Reset - Medicine Reminder",
        f"Hello,\n\nClick this link to reset your password:\n{reset_link}\n\nThis link expires in 30 minutes."
    )
    return jsonify({"success": True, "message": "✅ Reset link sent! Check your email."})

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        return render_template("reset_password.html")

    data = request.get_json(force=True)
    token = data.get("token")
    new_password = data.get("password")

    email = serializer.loads(token, salt="password-reset-salt", max_age=1800)
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "error": "User not found."})

    hashed_pw = generate_password_hash(new_password)
    users_col.update_one({"email": email}, {"$set": {"password": hashed_pw}})
    session["username"] = user["username"]
    return jsonify({"success": True, "message": "Password updated successfully."})

# ======================
# Automatic Daily Reminder Scheduler
# ======================
IST = pytz.timezone("Asia/Kolkata")

def matches_period(timing_field, period):
    if not timing_field:
        return False
    text = timing_field.lower()
    patterns = {
        "morning": r"morning|am|breakfast",
        "afternoon": r"afternoon|noon|lunch",
        "night": r"night|pm|evening|dinner|bedtime"
    }
    return re.search(patterns[period], text) is not None

def send_reminder_email(patient, period):
    try:
        msg = MIMEText(f"""
Hello {patient.get('patient_name', 'Patient')},

This is your {period} medicine reminder 💊

🩺 Disease: {patient.get('disease', 'N/A')}
💊 Medicine: {patient.get('medicine', 'N/A')}
💧 Dosage: {patient.get('dosage', 'N/A')}
⏰ Timing: {patient.get('time_to_take', 'N/A')}

Please take your medicine as prescribed.
Stay healthy! 💙

— Medicine Reminder System
""", "plain", "utf-8")

        msg["Subject"] = f"💊 {period.capitalize()} Medicine Reminder"
        msg["From"] = SENDER_EMAIL
        msg["To"] = patient["email"]

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print(f"✅ {period.capitalize()} reminder sent to {patient['email']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send reminder to {patient['email']}: {e}")
        return False

def run_reminder_job(period):
    today_str = date.today().isoformat()
    patients = list(patients_col.find({}))
    sent_count = 0

    for p in patients:
        timing = p.get("time_to_take", "")
        if matches_period(timing, period):
            meta_field = f"last_sent_{period}"
            if p.get(meta_field) == today_str:
                continue
            if send_reminder_email(p, period):
                sent_count += 1
                patients_col.update_one({"_id": p["_id"]}, {"$set": {meta_field: today_str}})

    print(f"📅 {period.capitalize()} reminders completed. Sent: {sent_count}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(run_reminder_job, "cron", args=["morning"], hour=8, minute=0, id="reminder_morning")
    scheduler.add_job(run_reminder_job, "cron", args=["afternoon"], hour=13, minute=0, id="reminder_afternoon")
    scheduler.add_job(run_reminder_job, "cron", args=["night"], hour=20, minute=0, id="reminder_night")
    scheduler.start()
    print("🕒 Medicine Reminder Scheduler started successfully.")

# ======================
# Safe entry point
# ======================
def main():
    """Main entry point when running Flask directly."""
    start_scheduler()
    logger.info("🚀 Starting Flask (with Scheduler)")
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main()
