# data.py
# Central in-memory data store with optional persistence using shelve

from datetime import datetime
import os
import shelve

# ---------------------------
# Persistence
# ---------------------------
DATA_FILE = os.path.join(os.path.dirname(__file__), "data_store")

# ---------------------------
# Data containers
# ---------------------------
parked_buses = []
# Each bus: { bus_number, bus_type, route, owner, slot, entry_time }

drivers = []
# Each driver: { id, name, role, phone, email, license_number, assigned_bus }

TOTAL_SLOTS = 100
slots = [
    {"slot_number": i, "status": "available", "bus_number": None}
    for i in range(1, TOTAL_SLOTS + 1)
]

transactions = []
# Each transaction: { id, bus_number, entry_time, exit_time, duration_minutes,
#                     fee, discount, amount_paid, pass_used, recorded_by }

users = {
    "admin": {"password": "admin123", "role": "Admin",  "name": "Administrator"},
    "staff": {"password": "staff123", "role": "Staff",  "name": "Staff Member"},
}

# Session store (simple)
logged_in_user = {"username": None, "role": None, "name": None}


def load_data():
    """Load persisted data from disk if it exists."""
    global parked_buses, drivers, slots, transactions, users

    try:
        with shelve.open(DATA_FILE) as db:
            parked_buses = db.get("parked_buses", parked_buses)
            drivers = db.get("drivers", drivers)
            slots = db.get("slots", slots)
            transactions = db.get("transactions", transactions)
            users = db.get("users", users)
    except Exception:
        # If something goes wrong, continue with defaults.
        pass

    # Ensure the slots structure matches configured capacity (e.g. when TOTAL_SLOTS increases)
    if len(slots) < TOTAL_SLOTS:
        for i in range(len(slots) + 1, TOTAL_SLOTS + 1):
            slots.append({"slot_number": i, "status": "available", "bus_number": None})
    elif len(slots) > TOTAL_SLOTS:
        slots = [s for s in slots if s.get("slot_number", 0) <= TOTAL_SLOTS]


def save_data():
    """Persist the current data structures to disk."""
    try:
        with shelve.open(DATA_FILE) as db:
            db["parked_buses"] = parked_buses
            db["drivers"] = drivers
            db["slots"] = slots
            db["transactions"] = transactions
            db["users"] = users
    except Exception:
        # Ignore persistence failures; app can still run in-memory.
        pass


# Load persisted data on import
load_data()
