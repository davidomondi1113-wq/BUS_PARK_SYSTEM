# reports.py
# Generates revenue reports, occupancy stats, frequent buses/drivers, CSV export

import csv
import io
from datetime import datetime, timedelta
from collections import Counter
import data


def _parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _txns_in_range(start_date, end_date):
    result = []
    for t in data.transactions:
        d = _parse_date(t["date"])
        if start_date <= d <= end_date:
            result.append(t)
    return result


# ---------------------------
# Revenue Reports
# ---------------------------

def daily_report(date=None):
    date = date or datetime.now().date()
    txns = _txns_in_range(date, date)
    return {
        "period": str(date),
        "transactions": txns,
        "total_revenue": round(sum(t["amount_paid"] for t in txns), 2),
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
        "total_revenue": round(sum(t["amount_paid"] for t in txns), 2),
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
        "total_revenue": round(sum(t["amount_paid"] for t in txns), 2),
        "count": len(txns),
    }


# ---------------------------
# Occupancy Report
# ---------------------------

def occupancy_report():
    occupied = sum(1 for s in data.slots if s["status"] == "occupied")
    available = data.TOTAL_SLOTS - occupied
    pct = round((occupied / data.TOTAL_SLOTS) * 100, 1) if data.TOTAL_SLOTS else 0
    return {
        "total": data.TOTAL_SLOTS,
        "occupied": occupied,
        "available": available,
        "occupancy_pct": pct,
    }


# ---------------------------
# Frequent Buses & Drivers
# ---------------------------

def frequent_buses(top_n=5):
    counts = Counter(t["bus_number"] for t in data.transactions)
    return counts.most_common(top_n)


def frequent_drivers(top_n=5):
    counts = Counter(t["recorded_by"] for t in data.transactions)
    return counts.most_common(top_n)


# ---------------------------
# CSV Export
# ---------------------------

def export_transactions_csv():
    """Returns a CSV string of all transactions."""
    output = io.StringIO()
    fieldnames = ["id", "bus_number", "bus_type", "entry_time", "exit_time",
                  "duration_minutes", "gross_fee", "discount_pct",
                  "discount_amt", "amount_paid", "pass_used", "recorded_by", "date"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data.transactions)
    return output.getvalue()
