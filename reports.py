# reports.py
# Generates revenue reports, occupancy stats, frequent buses/drivers, CSV export

import csv
import io
from datetime import datetime, timedelta

from database import db
from models import Transaction, Slot


def _parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _txns_in_range(start_date, end_date):
    txns = Transaction.query.filter(
        Transaction.exit_time >= datetime.combine(start_date, datetime.min.time()),
        Transaction.exit_time <= datetime.combine(end_date, datetime.max.time())
    ).all()
    return txns


# ---------------------------
# Revenue Reports
# ---------------------------

def daily_report(date=None):
    date = date or datetime.now().date()
    txns = _txns_in_range(date, date)
    return {
        "period": str(date),
        "transactions": txns,
        "total_revenue": round(sum(t.amount_paid for t in txns), 2),
        "count": len(txns),
    }


def weekly_report(date=None):
    date = date or datetime.now().date()
    start = date - timedelta(days=date.weekday())
    end   = start + timedelta(days=6)
    txns  = _txns_in_range(start, end)
    return {
        "period": f"{start} to {end}",
        "transactions": txns,
        "total_revenue": round(sum(t.amount_paid for t in txns), 2),
        "count": len(txns),
    }


def monthly_report(year=None, month=None):
    now   = datetime.now()
    year  = year  or now.year
    month = month or now.month
    start = datetime(year, month, 1).date()
    if month == 12:
        end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    txns = _txns_in_range(start, end)
    return {
        "period": f"{year}-{month:02d}",
        "transactions": txns,
        "total_revenue": round(sum(t.amount_paid for t in txns), 2),
        "count": len(txns),
    }


# ---------------------------
# Occupancy Report
# ---------------------------

def occupancy_report():
    total = Slot.query.count()
    occupied = Slot.query.filter_by(status="occupied").count()
    available = max(total - occupied, 0)
    pct = round((occupied / total) * 100, 1) if total else 0
    return {
        "total": total,
        "occupied": occupied,
        "available": available,
        "occupancy_pct": pct,
    }


# ---------------------------
# Frequent Buses & Drivers
# ---------------------------

def frequent_buses(top_n=5):
    # Return most common bus_number in transactions
    rows = (
        db.session.query(Transaction.bus_number, db.func.count(Transaction.bus_number).label("count"))
        .group_by(Transaction.bus_number)
        .order_by(db.desc("count"))
        .limit(top_n)
        .all()
    )
    return [(r.bus_number, r.count) for r in rows]


def frequent_drivers(top_n=5):
    rows = (
        db.session.query(Transaction.recorded_by, db.func.count(Transaction.recorded_by).label("count"))
        .group_by(Transaction.recorded_by)
        .order_by(db.desc("count"))
        .limit(top_n)
        .all()
    )
    return [(r.recorded_by, r.count) for r in rows]


# ---------------------------
# CSV Export
# ---------------------------

def export_transactions_csv():
    """Returns a CSV string of all transactions."""
    output = io.StringIO()
    fieldnames = ["id", "bus_number", "bus_type", "entry_time", "exit_time",
                  "duration_minutes", "gross_fee", "discount_pct",
                  "discount_amt", "amount_paid", "pass_used", "recorded_by", "receipt_number", "driver_phone", "date"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for txn in Transaction.query.order_by(Transaction.id.desc()).all():
        writer.writerow(txn.to_dict())

    return output.getvalue()
