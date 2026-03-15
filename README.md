# 🚌 Kisumu Mpya Bus Park System

A modern web-based bus park management system built with **Python Flask** and **M-Pesa Daraja API**.

## Features
- 🚌 Bus Entry & Exit with automatic slot assignment
- 🅿️ Real-time parking slot tracking
- 👤 Driver & Conductor management
- 💚 **M-Pesa STK Push payment** at bus entry (Safaricom Daraja API)
- 💳 Fee calculation with pass discounts (Silver, Gold, Platinum)
- 📊 Daily, Weekly & Monthly revenue reports
- 📥 CSV export of transactions
- 🔐 Role-based login (Admin & Staff)
- 👥 User management (Admin only)
- 🗄️ SQLite database (via SQLAlchemy)

## Tech Stack
- Python 3.x
- Flask + Flask-SQLAlchemy + Flask-Migrate
- Safaricom Daraja API (M-Pesa STK Push)
- Jinja2 Templates
- HTML5 / CSS3 (Glassmorphism, Animations)
- Font Awesome Icons

## Setup & Run

```bash
# Install dependencies
pip install flask flask-sqlalchemy flask-migrate requests

# Run the app
python main.py
```

Visit: http://127.0.0.1:5000/login

## Default Credentials
| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | Admin |
| staff    | staff123 | Staff |

## M-Pesa Setup
Edit `mpesa.py` with your Daraja credentials from https://developer.safaricom.co.ke/

```python
CONSUMER_KEY    = "your_consumer_key"
CONSUMER_SECRET = "your_consumer_secret"
SHORTCODE       = "your_shortcode"
PASSKEY         = "your_passkey"
CALLBACK_URL    = "https://yourdomain.com/mpesa/callback"
```

For local testing, use [ngrok](https://ngrok.com):
```bash
ngrok http 5000
# Then set CALLBACK_URL = "https://xxxx.ngrok.io/mpesa/callback"
```

## M-Pesa Payment Flow
1. Staff fills in bus & driver details on `/bus_entry`
2. Clicks **Send STK Push** — driver receives M-Pesa prompt on phone
3. Driver enters PIN — payment confirmed automatically
4. **Record Bus Entry** button unlocks — slot assigned & receipt generated

## Project Structure
```
bus_park_system/
├── main.py           # Flask routes & app entry point
├── mpesa.py          # Safaricom Daraja API integration
├── data.py           # In-memory data helpers
├── database.py       # SQLAlchemy setup
├── models.py         # Database models
├── users.py          # Login & role-based access
├── transactions.py   # Fee calculation & payment recording
├── reports.py        # Revenue & occupancy reports
├── slots.py          # Parking slot management
├── drivers.py        # Driver & conductor management
├── styles.py         # CSS style constants
├── static/
│   └── images/
│       └── logo.png
└── templates/
    ├── home.html
    ├── login.html
    ├── bus_entry.html
    ├── bus_exit.html
    ├── receipt.html
    ├── slots.html
    ├── drivers.html
    ├── driver_form.html
    ├── transactions.html
    ├── reports.html
    └── users.html
```

## Designed by
**Daose David** | © 2026 Kisumu Mpya Bus Park
