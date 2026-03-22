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
from database import db
from models import Setting

# ── DB HELPER ────────────────────────────────────────────────────────────────
def get_mpesa_setting(key, default=""):
    """Get M-Pesa setting from DB, env var, or default. Safe without app context."""
    try:
        setting = Setting.query.get(key)
        if setting and setting.value is not None:
            return setting.value
    except Exception:
        # Possibly no app context / DB not ready
        pass

    # Translate mpesa_foo to MPESA_FOO env var
    env_key = key.upper()
    if env_key.startswith("MPESA_") is False:
        env_key = f"MPESA_{env_key}"
    return os.environ.get(env_key, default)


# ── MODE ──────────────────────────────────────────────────────────────────────
SIMULATION_MODE = get_mpesa_setting("mpesa_simulation_mode", "true").lower() == "true"   # True = local auto-confirm | False = real Daraja API

# ── CREDENTIALS (read from DB settings, fallback to defaults) ────────────────
CONSUMER_KEY    = get_mpesa_setting("mpesa_consumer_key",    "")
CONSUMER_SECRET = get_mpesa_setting("mpesa_consumer_secret", "")
SHORTCODE       = get_mpesa_setting("mpesa_shortcode",       "174379")
PASSKEY         = get_mpesa_setting("mpesa_passkey",         "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
CALLBACK_URL    = get_mpesa_setting("mpesa_callback_url",    "")

# ── DARAJA ENDPOINTS (sandbox) ────────────────────────────────────────────────
TOKEN_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_URL   = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
QUERY_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

# ── DB HELPER ────────────────────────────────────────────────────────────────
def get_mpesa_setting(key, default=""):
    """Get M-Pesa setting from DB or return default."""
    setting = Setting.query.get(key)
    return setting.value if setting else default

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
    CALLBACK_URL = get_mpesa_setting("mpesa_callback_url")
    if not CALLBACK_URL:
        return False, (
            "mpesa_callback_url not set. Go to /settings to configure."
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
    key    = get_mpesa_setting("mpesa_consumer_key")
    secret = get_mpesa_setting("mpesa_consumer_secret")
    if not key or not secret:
        print("[MPESA] Missing mpesa_consumer_key/mpesa_consumer_secret in settings. Go to /settings.")
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
    shortcode = get_mpesa_setting("mpesa_shortcode", "174379")
    passkey   = get_mpesa_setting("mpesa_passkey", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
    raw = f"{shortcode}{passkey}{timestamp}"
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

    CALLBACK_URL = get_mpesa_setting("mpesa_callback_url")
    ok, msg = _validate()
    if not ok:
        return {"success": False, "message": msg}

    token = _get_access_token()
    if not token:
        return {"success": False, "message": "Failed to get M-Pesa access token. Check credentials."}

    shortcode = get_mpesa_setting("mpesa_shortcode", "174379")
    passkey   = get_mpesa_setting("mpesa_passkey", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
    callback  = get_mpesa_setting("mpesa_callback_url")

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
    shortcode = get_mpesa_setting("mpesa_shortcode", "174379")
    payload = {
        "BusinessShortCode": shortcode,
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
