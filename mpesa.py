# mpesa.py — Safaricom Daraja API (STK Push)
#
# SIMULATION_MODE = True  → auto-confirm locally, no API call, no credentials needed
# SIMULATION_MODE = False → real Daraja API (driver gets phone popup)
#
# To run with real STK Push:
#   1. Set SIMULATION_MODE = False
#   2. Set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET env vars (from developer.safaricom.co.ke)
#   3. Set MPESA_CALLBACK_URL env var to your public HTTPS URL ending with /mpesa/callback
#      e.g.  set MPESA_CALLBACK_URL=https://xxxx.ngrok-free.app/mpesa/callback
#   4. Run: python main.py

import os
import base64
import uuid
import requests
from datetime import datetime

# ── MODE ──────────────────────────────────────────────────────────────────────
SIMULATION_MODE = False   # True = local auto-confirm | False = real Daraja API

# ── CREDENTIALS (read from env vars, fallback to placeholders) ────────────────
CONSUMER_KEY    = os.environ.get("MPESA_CONSUMER_KEY",    "")
CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
SHORTCODE       = os.environ.get("MPESA_SHORTCODE",       "174379")
PASSKEY         = os.environ.get("MPESA_PASSKEY",         "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
CALLBACK_URL    = os.environ.get("MPESA_CALLBACK_URL",    "")

# ── DARAJA ENDPOINTS (sandbox) ────────────────────────────────────────────────
TOKEN_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_URL   = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
QUERY_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

# ── In-memory simulation store ────────────────────────────────────────────────
_sim_payments = {}


# ── SIMULATION ────────────────────────────────────────────────────────────────
def _sim_stk_push(phone, amount, account_ref, description):
    checkout_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
    _sim_payments[checkout_id] = "pending"
    return {
        "success":     True,
        "message":     f"[SIMULATION] STK Push sent to {phone}. Payment will auto-confirm.",
        "checkout_id": checkout_id,
        "simulated":   True,
    }

def _sim_query(checkout_id):
    if checkout_id not in _sim_payments:
        return {"success": False, "paid": False, "message": "Unknown checkout ID."}
    _sim_payments[checkout_id] = "confirmed"
    return {"success": True, "paid": True, "message": "[SIMULATION] Payment confirmed.", "simulated": True}


# ── VALIDATION ────────────────────────────────────────────────────────────────
def _validate():
    """Return (ok, error_message). Called before every real STK Push."""
    if not CALLBACK_URL:
        return False, (
            "CALLBACK_URL is not set. "
            "Run: set MPESA_CALLBACK_URL=https://xxxx.ngrok-free.app/mpesa/callback "
            "then restart the server."
        )
    if CALLBACK_URL.startswith("https://your") or "placeholder" in CALLBACK_URL:
        return False, (
            "CALLBACK_URL is still the placeholder. "
            "Set MPESA_CALLBACK_URL to your ngrok URL ending with /mpesa/callback."
        )
    if not CALLBACK_URL.startswith("https://"):
        return False, "CALLBACK_URL must use HTTPS. Use ngrok to get a public HTTPS URL."
    if not CALLBACK_URL.endswith("/mpesa/callback"):
        return False, "CALLBACK_URL must end with /mpesa/callback."
    return True, ""


# ── DARAJA HELPERS ────────────────────────────────────────────────────────────
def _get_access_token():
    key    = os.environ.get("MPESA_CONSUMER_KEY")    or CONSUMER_KEY
    secret = os.environ.get("MPESA_CONSUMER_SECRET") or CONSUMER_SECRET
    if not key or not secret:
        print("[MPESA] Missing MPESA_CONSUMER_KEY/MPESA_CONSUMER_SECRET environment variables.")
        return None

    creds = base64.b64encode(f"{key}:{secret}".encode()).decode()
    try:
        res = requests.get(TOKEN_URL, headers={"Authorization": f"Basic {creds}"}, timeout=10)
        if res.status_code != 200:
            print(f"[MPESA] Token request failed (status {res.status_code}): {res.text}")
            return None
        token = res.json().get("access_token")
        print(f"[MPESA] Token fetched: {token[:10] if token else 'NONE'}")
        return token
    except Exception as e:
        print(f"[MPESA] Token error: {e}")
        return None

def _generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{SHORTCODE}{PASSKEY}{timestamp}"
    return base64.b64encode(raw.encode()).decode(), timestamp

def format_phone(phone):
    """Normalize phone to 254XXXXXXXXX format."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]
    return phone


# ── PUBLIC API ────────────────────────────────────────────────────────────────
def stk_push(phone, amount, account_ref, description="Parking Fee"):
    if SIMULATION_MODE:
        return _sim_stk_push(phone, amount, account_ref, description)

    ok, msg = _validate()
    if not ok:
        return {"success": False, "message": msg}

    token = _get_access_token()
    if not token:
        return {"success": False, "message": "Failed to get M-Pesa access token. Check credentials."}

    shortcode = os.environ.get("MPESA_SHORTCODE") or SHORTCODE
    passkey   = os.environ.get("MPESA_PASSKEY")   or PASSKEY
    callback  = os.environ.get("MPESA_CALLBACK_URL") or CALLBACK_URL

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password  = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()
    phone     = format_phone(phone)

    payload = {
        "BusinessShortCode": shortcode,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),
        "PartyA":            phone,
        "PartyB":            shortcode,
        "PhoneNumber":       phone,
        "CallBackURL":       callback,
        "AccountReference":  account_ref[:12],
        "TransactionDesc":   description[:13],
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        res  = requests.post(STK_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        print(f"[MPESA] STK response: {data}")
        if data.get("ResponseCode") == "0":
            return {
                "success":     True,
                "message":     "STK Push sent. Driver should see M-Pesa PIN prompt on their phone.",
                "checkout_id": data.get("CheckoutRequestID"),
                "merchant_id": data.get("MerchantRequestID"),
            }
        return {"success": False, "message": data.get("errorMessage") or data.get("ResponseDescription", "STK Push failed.")}
    except Exception as e:
        print(f"[MPESA] STK exception: {e}")
        return {"success": False, "message": f"Network error: {e}"}


def query_stk(checkout_request_id):
    if SIMULATION_MODE:
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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        res  = requests.post(QUERY_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        code = data.get("ResultCode")
        if code == "0" or code == 0:
            return {"success": True, "paid": True,  "message": "Payment confirmed."}
        if code == "1032":
            return {"success": True, "paid": False, "message": "Payment cancelled by user."}
        if code == "1037":
            return {"success": True, "paid": False, "message": "Payment request timed out."}
        return {"success": True, "paid": False, "message": data.get("ResultDesc", "Pending.")}
    except Exception as e:
        return {"success": False, "paid": False, "message": f"Query error: {e}"}
