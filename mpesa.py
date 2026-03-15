# mpesa.py
# Safaricom Daraja API - M-Pesa STK Push
# SANDBOX_MODE = True  → simulates payment locally (no real credentials needed)
# SANDBOX_MODE = False → uses real Daraja API (set your credentials below)

import requests
import base64
import uuid
from datetime import datetime

# -----------------------------------------------
# SET THIS TO False WHEN YOU HAVE REAL CREDENTIALS
# -----------------------------------------------
SANDBOX_MODE = True

# -----------------------------------------------
# DARAJA CREDENTIALS
# Get yours from https://developer.safaricom.co.ke/
# -----------------------------------------------
CONSUMER_KEY    = "your_consumer_key_here"
CONSUMER_SECRET = "your_consumer_secret_here"
SHORTCODE       = "174379"
PASSKEY         = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
CALLBACK_URL    = "https://yourdomain.com/mpesa/callback"

# Daraja endpoints
TOKEN_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_URL   = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
QUERY_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

# In-memory store for simulated payments { checkout_id: status }
_sim_payments = {}


# -----------------------------------------------
# SIMULATION MODE (no real credentials needed)
# -----------------------------------------------
def _sim_stk_push(phone, amount, account_ref, description):
    """Simulate an STK push — auto-confirms after first query."""
    checkout_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
    _sim_payments[checkout_id] = "pending"
    return {
        "success":     True,
        "message":     f"[SIMULATION] STK Push sent to {phone}. Payment will auto-confirm.",
        "checkout_id": checkout_id,
        "simulated":   True,
    }


def _sim_query(checkout_id):
    """Simulate payment confirmation — confirms on first query."""
    if checkout_id not in _sim_payments:
        return {"success": False, "paid": False, "message": "Unknown checkout ID."}
    # Auto-confirm on first query
    _sim_payments[checkout_id] = "confirmed"
    return {
        "success":  True,
        "paid":     True,
        "message":  "[SIMULATION] Payment confirmed automatically.",
        "simulated": True,
    }


# -----------------------------------------------
# REAL DARAJA API
# -----------------------------------------------
def _get_access_token():
    credentials = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()
    try:
        res = requests.get(
            TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        print(f"[MPESA] Token error: {e}")
        return None


def _generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw       = f"{SHORTCODE}{PASSKEY}{timestamp}"
    password  = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def format_phone(phone):
    """Normalize phone to 254XXXXXXXXX format."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]
    return phone


# -----------------------------------------------
# PUBLIC API — called by main.py
# -----------------------------------------------
def stk_push(phone, amount, account_ref, description="Parking Fee"):
    """Trigger STK Push. Uses simulation if SANDBOX_MODE=True."""
    if SANDBOX_MODE:
        return _sim_stk_push(phone, amount, account_ref, description)

    token = _get_access_token()
    if not token:
        return {"success": False, "message": "Failed to get M-Pesa access token. Check credentials."}

    password, timestamp = _generate_password()
    phone = format_phone(phone)

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),
        "PartyA":            phone,
        "PartyB":            SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       CALLBACK_URL,
        "AccountReference":  account_ref[:12],
        "TransactionDesc":   description[:13],
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    try:
        res  = requests.post(STK_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        if data.get("ResponseCode") == "0":
            return {
                "success":     True,
                "message":     "STK Push sent. Ask driver to check their phone.",
                "checkout_id": data.get("CheckoutRequestID"),
                "merchant_id": data.get("MerchantRequestID"),
            }
        return {
            "success": False,
            "message": data.get("errorMessage") or data.get("ResponseDescription", "STK Push failed."),
        }
    except Exception as e:
        return {"success": False, "message": f"Network error: {e}"}


def query_stk(checkout_request_id):
    """Query payment status. Uses simulation if SANDBOX_MODE=True."""
    if SANDBOX_MODE:
        return _sim_query(checkout_request_id)

    token = _get_access_token()
    if not token:
        return {"success": False, "paid": False, "message": "Token error."}

    password, timestamp = _generate_password()
    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    try:
        res  = requests.post(QUERY_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        code = data.get("ResultCode")
        if code == "0" or code == 0:
            return {"success": True,  "paid": True,  "message": "Payment confirmed."}
        elif code == "1032":
            return {"success": True,  "paid": False, "message": "Payment cancelled by user."}
        elif code == "1037":
            return {"success": True,  "paid": False, "message": "Payment request timed out."}
        return {"success": True, "paid": False, "message": data.get("ResultDesc", "Pending.")}
    except Exception as e:
        return {"success": False, "paid": False, "message": f"Query error: {e}"}
