"""
Radioactive Water Predictor — Configuration
============================================
Centralized settings for WiFi, server, email, SMS, and NGO contacts.
Update these values before deploying.
"""

# ─── Server Configuration ───
SERVER_HOST = "0.0.0.0"       # Binds to all interfaces (accessible from LAN)
SERVER_PORT = 5000
DEBUG_MODE = True

# ─── Gmail SMTP Configuration (for NGO Alerts) ───
# To use Gmail:
# 1. Enable 2-Step Verification on your Google Account
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Generate an "App Password" for "Mail"
# 4. Paste the 16-character password below
GMAIL_USER = "autismscreening18@gmail.com"
GMAIL_APP_PASSWORD = "gopbgvpbccmmihht"

# ─── NGO Contact Information ───
NGO_EMAILS = [
    "karthikristen@gmail.com",
]

# ─── Twilio SMS Configuration (Optional Fallback) ───
# Sign up at https://www.twilio.com/ for a free trial
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_FROM_NUMBER = ""   # e.g., "+1234567890"
NGO_PHONE_NUMBERS = []     # e.g., ["+919876543210"]

# ─── Alert Rate Limiting ───
ALERT_COOLDOWN_MINUTES = 10   # Minimum time between alerts

# ─── Sensor Configuration ───
SENSOR_POLL_INTERVAL_MS = 5000   # How often ESP32 sends data (milliseconds)
SENSOR_TIMEOUT_SECONDS = 15      # Mark ESP32 as disconnected after this

# ─── WHO Safe Ranges for Reference ───
SAFE_RANGES = {
    "tds":          {"min": 0,   "max": 500,  "unit": "mg/L"},
    "ph":           {"min": 6.5, "max": 8.5,  "unit": ""},
    "hardness":     {"min": 0,   "max": 200,  "unit": "mg/L CaCO₃"},
    "nitrate":      {"min": 0,   "max": 45,   "unit": "mg/L"},
    "sulfate":      {"min": 0,   "max": 250,  "unit": "mg/L"},
    "chloride":     {"min": 0,   "max": 250,  "unit": "mg/L"},
    "conductivity": {"min": 0,   "max": 800,  "unit": "µS/cm"},
    "turbidity":    {"min": 0,   "max": 5,    "unit": "NTU"},
}
