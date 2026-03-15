# mpesa.py
# Safaricom Daraja API - M-Pesa STK Push (Lipa Na M-Pesa Online)

import requests
import base64
from datetime import datetime

# -----------------------------------------------
# DARAJA CREDENTIALS — Replace with your own from
# https://developer.safaricom.co.ke/
# -----------------------------------------------
CONSUMER_KEY    = "your_consumer_key_here"
CONSUMER_SECRET = "your_consumer_secret_here"
SHORTCODE       = "174379"           # Daraja sandbox shortcode
PASSKEY         = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Sandbox passkey
CALLBACK_URL    = "https://yourdomain.com/mpesa/callback"  # Must be HTTPS in production
                                                            # Use ngrok for local testing

# Sandbox endpoints
TOKEN_URL   = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_URL     = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
QUERY_URL   = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"


def _get_access_token():
    """Get OAuth access token from Daraja."""
    credentials = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    try:
        res = requests.get(TOKEN_URL, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        print(f"[MPESA] Token error: {e}")
        return None


def _generate_password():
    """Generate base64 encoded password for STK push."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{SHORTCODE}{PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def format_phone(phone):
    """Normalize phone number to 254XXXXXXXXX format."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]
    return phone


def stk_push(phone, amount, account_ref, description="Parking Fee"):
    """
    Trigger M-Pesa STK Push to driver's phone.
    Returns dict with success status and response data.
    """
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
        "AccountReference":  account_ref[:12],   # max 12 chars
        "TransactionDesc":   description[:13],   # max 13 chars
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    try:
        res = requests.post(STK_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        if data.get("ResponseCode") == "0":
            return {
                "success":        True,
                "message":        "STK Push sent. Ask driver to check their phone.",
                "checkout_id":    data.get("CheckoutRequestID"),
                "merchant_id":    data.get("MerchantRequestID"),
            }
        else:
            return {
                "success": False,
                "message": data.get("errorMessage") or data.get("ResponseDescription", "STK Push failed."),
            }
    except Exception as e:
        return {"success": False, "message": f"Network error: {e}"}


def query_stk(checkout_request_id):
    """
    Query the status of an STK Push request.
    Returns dict with payment status.
    """
    token = _get_access_token()
    if not token:
        return {"success": False, "message": "Token error."}

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
        res = requests.post(QUERY_URL, json=payload, headers=headers, timeout=15)
        data = res.json()
        result_code = data.get("ResultCode")
        if result_code == "0" or result_code == 0:
            return {"success": True,  "paid": True,  "message": "Payment confirmed."}
        elif result_code == "1032":
            return {"success": True,  "paid": False, "message": "Payment cancelled by user."}
        elif result_code == "1037":
            return {"success": True,  "paid": False, "message": "Payment request timed out."}
        else:
            return {"success": True,  "paid": False, "message": data.get("ResultDesc", "Pending or failed.")}
    except Exception as e:
        return {"success": False, "paid": False, "message": f"Query error: {e}"}
