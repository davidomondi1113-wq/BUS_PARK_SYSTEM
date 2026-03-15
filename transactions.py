# transactions.py
# Handles parking fee calculation, payment recording, discounts, and passes

from datetime import datetime

from models import db, Transaction

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


def calculate_fee(bus_type, entry_time, exit_time, pass_type="None", fixed_fee=None):
    """Calculate parking fee based on duration, bus type, and pass discount.

    When `fixed_fee` is provided, the fee is fixed (e.g., an upfront payment)
    and duration-based calculation is not performed.
    """
    if fixed_fee is not None:
        gross_fee = fixed_fee
        minutes = 0
    else:
        duration = exit_time - entry_time
        minutes = max(int(duration.total_seconds() / 60), 1)
        hours = minutes / 60
        rate = FEE_RATES.get(bus_type, FEE_RATES["Unknown"])
        gross_fee = round(hours * rate, 2)
        gross_fee = max(gross_fee, MINIMUM_FEE)

    discount_pct = PASS_TYPES.get(pass_type, 0)
    discount_amt = round(gross_fee * discount_pct / 100, 2)
    amount_paid = round(gross_fee - discount_amt, 2)

    return {
        "duration_minutes": minutes,
        "gross_fee": gross_fee,
        "discount_pct": discount_pct,
        "discount_amt": discount_amt,
        "amount_paid": amount_paid,
    }


def record_transaction(bus_number, bus_type, entry_time, exit_time,
                       pass_type="None", recorded_by="staff",
                       receipt_number=None, driver_phone=None, fixed_fee=None):
    """Record a parking transaction into the database."""
    fee_info = calculate_fee(bus_type, entry_time, exit_time, pass_type, fixed_fee=fixed_fee)

    txn = Transaction(
        bus_number=bus_number,
        bus_type=bus_type,
        entry_time=entry_time,
        exit_time=exit_time,
        duration_minutes=fee_info["duration_minutes"],
        gross_fee=fee_info["gross_fee"],
        discount_pct=fee_info["discount_pct"],
        discount_amt=fee_info["discount_amt"],
        amount_paid=fee_info["amount_paid"],
        pass_used=pass_type,
        recorded_by=recorded_by,
        receipt_number=receipt_number,
        driver_phone=driver_phone,
    )
    db.session.add(txn)
    db.session.commit()
    return txn.to_dict()


def get_all_transactions():
    return [t.to_dict() for t in Transaction.query.order_by(Transaction.id.desc()).all()]


def get_transaction_by_id(txn_id):
    txn = Transaction.query.get(txn_id)
    return txn.to_dict() if txn else None


def get_transaction_by_receipt(receipt_number):
    txn = Transaction.query.filter_by(receipt_number=receipt_number).first()
    return txn.to_dict() if txn else None


def get_total_revenue():
    total = db.session.query(db.func.sum(Transaction.amount_paid)).scalar() or 0
    return round(total, 2)
