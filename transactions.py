# transactions.py
# Handles parking fee calculation, payment recording, discounts, and passes

from datetime import datetime
import data

_next_id = 1

# Fee rates (Ksh per hour by bus type)
FEE_RATES = {
    "Express":  50,
    "Shuttle":  40,
    "Standard": 30,
    "Unknown":  30,
}

# Discount rates by pass type
PASS_TYPES = {
    "None":    0,
    "Silver":  10,   # 10% off
    "Gold":    20,   # 20% off
    "Platinum":35,   # 35% off
}

MINIMUM_FEE = 50  # Ksh — minimum charge regardless of duration


def _new_id():
    global _next_id
    id_ = _next_id
    _next_id += 1
    return id_


def calculate_fee(bus_type, entry_time, exit_time, pass_type="None"):
    """Calculate parking fee based on duration, bus type, and pass discount."""
    duration = exit_time - entry_time
    minutes = max(int(duration.total_seconds() / 60), 1)
    hours = minutes / 60

    rate = FEE_RATES.get(bus_type, FEE_RATES["Unknown"])
    gross_fee = round(hours * rate, 2)
    gross_fee = max(gross_fee, MINIMUM_FEE)

    discount_pct = PASS_TYPES.get(pass_type, 0)
    discount_amt = round(gross_fee * discount_pct / 100, 2)
    amount_paid  = round(gross_fee - discount_amt, 2)

    return {
        "duration_minutes": minutes,
        "gross_fee": gross_fee,
        "discount_pct": discount_pct,
        "discount_amt": discount_amt,
        "amount_paid": amount_paid,
    }


def record_transaction(bus_number, bus_type, entry_time, exit_time,
                       pass_type="None", recorded_by="staff"):
    fee_info = calculate_fee(bus_type, entry_time, exit_time, pass_type)
    txn = {
        "id":               _new_id(),
        "bus_number":       bus_number,
        "bus_type":         bus_type,
        "entry_time":       entry_time.strftime("%Y-%m-%d %H:%M"),
        "exit_time":        exit_time.strftime("%Y-%m-%d %H:%M"),
        "duration_minutes": fee_info["duration_minutes"],
        "gross_fee":        fee_info["gross_fee"],
        "discount_pct":     fee_info["discount_pct"],
        "discount_amt":     fee_info["discount_amt"],
        "amount_paid":      fee_info["amount_paid"],
        "pass_used":        pass_type,
        "recorded_by":      recorded_by,
        "date":             exit_time.strftime("%Y-%m-%d"),
    }
    data.transactions.append(txn)
    data.save_data()
    return txn


def get_all_transactions():
    return data.transactions


def get_transaction_by_id(txn_id):
    for t in data.transactions:
        if t["id"] == txn_id:
            return t
    return None


def get_total_revenue():
    return round(sum(t["amount_paid"] for t in data.transactions), 2)
