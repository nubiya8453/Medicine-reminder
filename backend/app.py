# backend/app.py — Flask REST API Server with CORS and ML Recommender
from flask import Flask, request, jsonify, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import logging
import os
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer
from datetime import date
import pytz
import re

from recommender import Recommender
import scheduler

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecretkey")

# Enable CORS for frontend origin
CORS(app, supports_credentials=True, origins=["*"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medicine_app_api")

# MongoDB setup
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

# Initialize Recommender
try:
    recommender = Recommender()
except Exception as e:
    logger.exception("⚠️ Failed to initialize recommender: %s", e)
    recommender = None

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "nubiyafathima0@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "wdnv typb geib rmfy")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5500")

serializer = URLSafeTimedSerializer(app.secret_key)

def get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()

# -------------------------
# API Routes
# -------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "database": "connected" if mongo and mongo.db else "disconnected",
        "recommender": "loaded" if recommender else "not loaded"
    })

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = get_request_data()
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not username or not email or not password:
            return jsonify({"error": "All fields (username, email, password) are required"}), 400

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
        logger.info("✅ Registered user: %s", username)
        return jsonify({"success": True, "message": "Registration successful", "username": username})
    except Exception as e:
        logger.exception("❌ Error in /api/register: %s", e)
        return jsonify({"error": "Server error during registration"}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = get_request_data()
        username_or_email = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username_or_email or not password:
            return jsonify({"error": "Username/email and password are required"}), 400

        if users_col is None:
            return jsonify({"error": "Database not connected"}), 500

        user = users_col.find_one({
            "$or": [
                {"username": {"$regex": f"^{re.escape(username_or_email)}$", "$options": "i"}},
                {"email": {"$regex": f"^{re.escape(username_or_email)}$", "$options": "i"}}
            ]
        })

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Incorrect password"}), 401

        session["username"] = user["username"]
        session["email"] = user["email"]
        logger.info("✅ Login successful for: %s", user["username"])
        return jsonify({"success": True, "username": user["username"], "email": user["email"]})
    except Exception as e:
        logger.exception("❌ Error in /api/login: %s", e)
        return jsonify({"error": "Server error during login"}), 500

@app.route("/api/me", methods=["GET"])
def get_current_user():
    if "username" in session:
        return jsonify({"authenticated": True, "username": session["username"], "email": session.get("email")})
    return jsonify({"authenticated": False}), 401

@app.route("/api/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        data = get_request_data()
        patient_name = (data.get("patient_name") or "").strip()
        age = data.get("age")
        gender = data.get("gender")
        email = (data.get("email") or "").strip()
        disease = (data.get("disease") or "").strip()

        if not patient_name or not email or not disease:
            return jsonify({"error": "Patient name, email, and disease are required"}), 400

        if not recommender:
            return jsonify({"error": "Recommender system unavailable"}), 500

        rec = recommender.recommend(disease)

        if patients_col is not None:
            patients_col.insert_one({
                "patient_name": patient_name,
                "age": age,
                "gender": gender,
                "email": email,
                "disease": rec.get("disease"),
                "medicine": rec.get("medicine"),
                "dosage": rec.get("dosage"),
                "time_to_take": rec.get("time_to_take"),
                "created_at": date.today().isoformat()
            })

        # Send Email Notification
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
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = SENDER_EMAIL
            msg["To"] = email

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
                smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                smtp.send_message(msg)
            logger.info("✅ Recommendation email sent successfully to %s", email)
        except Exception as mail_err:
            logger.warning("⚠️ Failed sending email: %s", mail_err)

        return jsonify({
            "success": True,
            "disease": rec.get("disease"),
            "medicine": rec.get("medicine", "N/A"),
            "dosage": rec.get("dosage", "N/A"),
            "timing": rec.get("time_to_take", "N/A")
        })
    except Exception as e:
        logger.exception("❌ Error in /api/recommend: %s", e)
        return jsonify({"success": False, "error": "Failed to generate recommendation"}), 500

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = get_request_data()
        email = (data.get("email") or "").strip().lower()
        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400

        if users_col is None:
            return jsonify({"success": False, "error": "Database not connected"}), 500

        user = users_col.find_one({"email": email})
        if not user:
            return jsonify({"success": False, "message": "If that email is registered, a reset link has been sent."})

        token = serializer.dumps(email, salt="password-reset-salt")
        reset_link = f"{FRONTEND_URL}/reset_password.html?token={token}"

        body = f"Hello,\n\nClick this link to reset your password:\n{reset_link}\n\nThis link expires in 30 minutes."
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = "🔑 Password Reset - Medicine Reminder"
        msg["From"] = SENDER_EMAIL
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        return jsonify({"success": True, "message": "✅ Password reset link sent! Check your email."})
    except Exception as e:
        logger.exception("❌ Error in /api/forgot-password: %s", e)
        return jsonify({"success": False, "error": "Failed to process request"}), 500

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    try:
        data = get_request_data()
        token = data.get("token")
        new_password = data.get("password")

        if not token or not new_password:
            return jsonify({"success": False, "error": "Token and new password are required"}), 400

        try:
            email = serializer.loads(token, salt="password-reset-salt", max_age=1800)
        except Exception:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 400

        if users_col is None:
            return jsonify({"success": False, "error": "Database not connected"}), 500

        user = users_col.find_one({"email": email})
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        hashed_pw = generate_password_hash(new_password)
        users_col.update_one({"email": email}, {"$set": {"password": hashed_pw}})
        session["username"] = user["username"]
        return jsonify({"success": True, "message": "Password updated successfully."})
    except Exception as e:
        logger.exception("❌ Error in /api/reset-password: %s", e)
        return jsonify({"success": False, "error": "Failed to reset password"}), 500

def main():
    try:
        scheduler.start_scheduler()
    except Exception as e:
        logger.warning("⚠️ Background scheduler warning: %s", e)

    logger.info("🚀 Starting Medicine Reminder Flask REST API")
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main()
