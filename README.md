# 🚌 Kisumu Mpya Bus Park System

A modern web-based bus park management system built with **Python Flask**.

## Features
- 🚌 Bus Entry & Exit with automatic slot assignment
- 🅿️ Real-time parking slot tracking (20 slots)
- 👤 Driver & Conductor management
- 💳 Fee calculation with pass discounts (Silver, Gold, Platinum)
- 📊 Daily, Weekly & Monthly revenue reports
- 📥 CSV export of transactions
- 🔐 Role-based login (Admin & Staff)
- 👥 User management (Admin only)

## Tech Stack
- Python 3.x
- Flask
- Jinja2 Templates
- HTML5 / CSS3 (Glassmorphism, Animations)
- Font Awesome Icons

## Setup & Run

```bash
# Install dependencies
pip install flask

# Run the app
python main.py
```

Visit: http://127.0.0.1:5000/login

## Default Credentials
| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | Admin |
| staff    | staff123 | Staff |

## Project Structure
```
bus_park_system/
├── main.py          # Flask routes & app entry point
├── data.py          # Central in-memory data store
├── users.py         # Login & role-based access
├── transactions.py  # Fee calculation & payment recording
├── reports.py       # Revenue & occupancy reports
├── slots.py         # Parking slot management
├── drivers.py       # Driver & conductor management
├── styles.py        # CSS style constants
├── static/
│   └── images/
│       └── logo.png
└── templates/
    ├── home.html
    ├── login.html
    ├── bus_entry.html
    ├── bus_exit.html
    ├── slots.html
    ├── drivers.html
    ├── driver_form.html
    ├── transactions.html
    ├── reports.html
    └── users.html
```

## Designed by
**Daose David** | © 2026 Kisumu Mpya Bus Park
