"""
scheduler.py — Medicine Reminder Mailer
---------------------------------------
Run this script alongside your Flask app to send full patient
and medicine details to the patient's email.

✅ Sends all details (name, age, gender, email, disease, medicine, dosage, timing, notes)
✅ Automatically checks MongoDB
✅ Logs success/failure clearly
✅ Supports Gmail App Passwords
"""

import logging
from datetime import date
import pytz
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
import re
import time

# --------------------
# Configuration
# --------------------
MONGO_URI = "mongodb://127.0.0.1:27017/medicine_reminder"
DB_NAME = "medicine_reminder"
PATIENTS_COLLECTION = "patients"

SENDER_EMAIL = "nubiyafathima0@gmail.com"          # ← your Gmail
SENDER_PASSWORD = "wdnv typb geib rmfy" # ← Gmail App Password

# India time
TZ = pytz.timezone("Asia/Kolkata")

# Send reminder times (IST)
SCHEDULE = {
    "morning": {"hour": 8, "minute": 0},
    "afternoon": {"hour": 13, "minute": 0},
    "night": {"hour": 20, "minute": 0},
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MedicineReminder")

# --------------------
# Helper Functions
# --------------------
def connect_db():
    """Connect to MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db, client


def patient_matches_period(patient_timing_field: str, period: str) -> bool:
    """Check if the patient's timing text mentions the given period."""
    if not patient_timing_field:
        return False
    text = patient_timing_field.lower()
    patterns = {
        "morning": r"morning|morn|am|breakfast",
        "afternoon": r"afternoon|noon|midday|pm|lunch",
        "night": r"night|evening|bedtime|dinner"
    }
    return re.search(patterns.get(period, ""), text) is not None


def send_email(to_email: str, subject: str, body: str):
    """Send a formatted email."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logger.info(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return False


# --------------------
# Main Reminder Function
# --------------------
def send_batch_for_period(period: str):
    """Send full patient + medicine detail reminders for a given period."""
    db, client = connect_db()
    patients_col = db[PATIENTS_COLLECTION]
    today_str = date.today().isoformat()

    logger.info(f"🔹 Running reminder job for {period} ({today_str})")

    sent_count = 0
    fail_count = 0

    cursor = patients_col.find({})
    for p in cursor:
        # Prefer 'time_to_take' (new field), then fall back to 'timing' or 'timings'
        timing_field = (p.get("time_to_take") or p.get("timing") or p.get("timings") or "")
        timing_field_lc = timing_field.lower() if isinstance(timing_field, str) else ""

        if not patient_matches_period(timing_field_lc, period):
            continue

        # Skip if already sent today
        meta_field = f"last_sent_{period}"
        if p.get(meta_field) == today_str:
            continue

        # Extract all details
        patient_name = p.get("patient_name", "Unknown")
        age = p.get("age", "N/A")
        gender = p.get("gender", "N/A")
        email = p.get("email", "N/A")
        disease = p.get("disease", "N/A")
        medicine = p.get("medicine", p.get("medicine_suggestion", "N/A"))
        dosage = p.get("dosage", "N/A")
        # Use time_to_take first, then other fields
        timing_text = p.get("time_to_take", p.get("timing", p.get("timings", "N/A")))
        notes = p.get("notes", "No additional notes provided.")
        created_at = p.get("created_at", today_str)

        # Build email content
        subject = f"💊 Medicine Reminder — {patient_name} ({str(disease).capitalize()})"
        body = f"""
Hello {patient_name},

This is your scheduled medicine reminder for the {period}.

🧍 PATIENT DETAILS
--------------------------------
👤 Name: {patient_name}
🎂 Age: {age}
⚧ Gender: {gender}
📧 Email: {email}

🩺 MEDICAL INFORMATION
--------------------------------
🦠 Disease: {str(disease).capitalize()}
💊 Medicine: {str(medicine).capitalize()}
💧 Dosage: {dosage}
⏰ Timing: {timing_text}
🗒️ Notes: {notes}

📅 Record Created: {created_at}
📩 Reminder Sent On: {today_str}

Please take your medicine as prescribed.
If you feel unwell, consult your doctor immediately.

— Medicine Reminder System 💊
"""

        if not email or "@" not in str(email):
            logger.warning(f"Skipping invalid email for {patient_name}: {email}")
            continue

        ok = send_email(email, subject, body)
        if ok:
            sent_count += 1
            patients_col.update_one(
                {"_id": p["_id"]},
                {"$set": {meta_field: today_str}}
            )
        else:
            fail_count += 1

    client.close()
    logger.info(f"✅ Completed {period} reminders — Sent: {sent_count}, Failed: {fail_count}")


# --------------------
# Scheduler Setup
# --------------------
def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TZ)

    for period, when in SCHEDULE.items():
        scheduler.add_job(
            send_batch_for_period,
            trigger="cron",
            args=[period],
            hour=when["hour"],
            minute=when["minute"],
            id=f"reminder_{period}",
            replace_existing=True
        )
        logger.info(f"📅 Scheduled {period} reminders at {when['hour']:02d}:{when['minute']:02d} {TZ}")

    scheduler.start()
    logger.info("✅ Scheduler started — press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Stopping scheduler...")
        scheduler.shutdown()


# --------------------
# Run immediately (for testing)
# --------------------
if __name__ == "__main__":
    logger.info("🚀 Starting Medicine Reminder Scheduler...")

    # 🔹 Send once immediately for testing
    send_batch_for_period("morning")

    # 🔹 Uncomment below line to enable automatic daily schedule
    # start_scheduler()
