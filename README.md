# 💊 Medicine Reminder System

A decoupled, full-stack medical application featuring an intelligent disease-to-medicine recommendation engine (TF-IDF + Fuzzy Matching), automated daily email reminders, user authentication, and a modern responsive user interface.

---

## 📁 Project Structure

```
medical/
├── backend/                            # Flask REST API + ML Engine + Scheduler
│   ├── app.py                          # Main REST API server
│   ├── recommender.py                  # TF-IDF + Cosine Similarity Recommender Engine
│   ├── scheduler.py                    # APScheduler background email reminder service
│   ├── disease_medicine_schedule.xlsx  # Medical dataset
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Environment variable configuration template
│
├── frontend/                           # Client-side Web Interface
│   ├── index.html                      # Authentication Page (Login / Register)
│   ├── dashboard.html                  # Main User Dashboard & Recommender UI
│   ├── forgot_password.html            # Forgot Password request page
│   ├── reset_password.html             # Reset Password confirmation page
│   ├── css/
│   │   └── style.css                   # Custom medical UI theme
│   └── js/
│       ├── api.js                      # API communication layer (Fetch API wrapper)
│       ├── auth.js                     # Authentication handler
│       ├── dashboard.js                # Recommender form & UI logic
│       └── reset.js                    # Password reset handler
│
└── README.md                           # Documentation
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ensure **MongoDB** is running locally on default port `27017` (or set `MONGO_URI` environment variable).

4. Start the Flask REST API backend server:
   ```bash
   python app.py
   ```
   The backend API will run at `http://127.0.0.1:5000`.

---

### 2. Frontend Setup

The frontend consists of static HTML/CSS/JavaScript files and communicates with the Flask backend via REST API endpoints.

You can launch the frontend using any static file server:

- **Option A (VS Code Live Server)**: Right-click `frontend/index.html` and select **Open with Live Server**.
- **Option B (Python HTTP Server)**:
  ```bash
  cd frontend
  python -m http.server 5500
  ```
  Then open `http://127.0.0.1:5500` in your web browser.

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check & system status |
| `POST` | `/api/register` | Register a new user |
| `POST` | `/api/login` | Authenticate user & open session |
| `GET` | `/api/me` | Check active session |
| `POST` | `/api/logout` | End session |
| `POST` | `/api/recommend` | Generate medicine recommendation & send email |
| `POST` | `/api/forgot-password` | Request password reset email |
| `POST` | `/api/reset-password` | Set new password with token |