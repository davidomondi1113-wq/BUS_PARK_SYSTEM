# main.py
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
from datetime import datetime
import uuid

from database import db
from models import User, Slot, Bus, Transaction, Driver, Setting
from flask_migrate import Migrate

import slots as slts
import transactions as txns
import drivers as drv
import users as usr
import reports as rpts
import mpesa

app = Flask(__name__)
app.secret_key = "kisumu_bus_park_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///buspark.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database extensions
db.init_app(app)
migrate = Migrate(app, db)

# ---------------------------
# Setup helpers
# ---------------------------
def ensure_default_user():
    """Ensure there is at least one user (admin) to log in with."""
    if User.query.count() == 0:
        admin = User(username="admin", password="admin123", role="Admin", name="Administrator")
        db.session.add(admin)
        db.session.commit()
        print("[INFO] Created default admin user: admin/admin123")


def _generate_receipt_number():
    """Generate a short, unique receipt number for parking payments."""
    return f"R{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def get_setting(key, default=None):
    setting = Setting.query.get(key)
    return setting.value if setting else default


def set_setting(key, value):
    setting = Setting.query.get(key)
    if not setting:
        setting = Setting(key=key, value=str(value))
        db.session.add(setting)
    else:
        setting.value = str(value)
    db.session.commit()


def ensure_settings():
    # Ensure there is a park name and slot count configured.
    set_setting("park_name", get_setting("park_name", "Kisumu Mpya Bus Park"))
    set_setting("total_slots", get_setting("total_slots", "100"))


def ensure_slots():
    # Ensure slots exist up to the configured total.
    total_slots = int(get_setting("total_slots", "100"))
    existing = {s.slot_number for s in Slot.query.all()}
    for i in range(1, total_slots + 1):
        if i not in existing:
            slot = Slot(slot_number=i, status="available")
            db.session.add(slot)
    db.session.commit()


# Ensure the database structure and minimal configuration exists on startup.
with app.app_context():
    db.create_all()
    ensure_settings()
    ensure_default_user()
    ensure_slots()


# ---------------------------
# Auth helpers
# ---------------------------
def current_user():
    return session.get("user")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------
# Login / Logout
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    setup_mode = User.query.count() == 0

    if setup_mode and request.method == "POST":
        # First-time setup: create the first admin user and configure park settings
        username = request.form.get("username", "admin").strip() or "admin"
        password = request.form.get("password", "admin123")
        name = request.form.get("name", "Administrator").strip() or "Administrator"

        park_name = request.form.get("park_name", "Kisumu Mpya Bus Park").strip() or "Kisumu Mpya Bus Park"
        try:
            total_slots = int(request.form.get("total_slots", 100))
        except ValueError:
            total_slots = 100

        set_setting("park_name", park_name)
        set_setting("total_slots", str(total_slots))
        ensure_slots()

        user = User(username=username, password=password, role="Admin", name=name)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    if request.method == "POST" and not setup_mode:
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            session["user"] = {"username": user.username, "role": user.role, "name": user.name}
            return redirect(url_for("home"))
        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error,
        setup=setup_mode,
        park_name=get_setting("park_name", "Kisumu Mpya Bus Park"),
        total_slots=get_setting("total_slots", "100"),
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------
# Home
# ---------------------------
@app.route("/")
@login_required
def home():
    occ = rpts.occupancy_report()
    parked_buses = Bus.query.filter_by(status="Parked").order_by(Bus.entry_time.desc()).all()
    return render_template("home.html",
        buses=parked_buses,
        occupancy=occ,
        total_revenue=txns.get_total_revenue(),
        park_name=get_setting("park_name", "Kisumu Mpya Bus Park"),
        user=current_user()
    )


# ---------------------------
# Bus Entry
# ---------------------------
@app.route("/bus_entry", methods=["GET", "POST"])
@login_required
def bus_entry():
    message = None
    msg_type = "success"
    if request.method == "POST":
        bus_number   = request.form["bus_number"].strip().upper()
        bus_type     = request.form.get("bus_type", "Standard")
        route        = request.form.get("route", "Unknown")
        owner        = request.form.get("owner", "Unknown")
        driver_name  = request.form.get("driver_name", "Unknown")
        driver_phone = request.form.get("driver_phone", "").strip()

        if not driver_phone:
            message  = "Driver phone number is required to process parking fee."
            msg_type = "error"
        elif Bus.query.filter_by(bus_number=bus_number, status="Parked").first():
            message  = f"Bus {bus_number} is already parked!"
            msg_type = "error"
        elif slts.is_full():
            message  = "⚠️ Park is FULL! No available slots."
            msg_type = "error"
        else:
            receipt = _generate_receipt_number()
            entry_time = datetime.now()
            slot = slts.assign_slot(bus_number)

            new_bus = Bus(
                bus_number=bus_number,
                bus_type=bus_type,
                route=route,
                owner=owner,
                slot_number=(slot.get("slot_number") if slot else None),
                entry_time=entry_time,
                status="Parked",
                receipt_number=receipt,
                driver_phone=driver_phone,
            )
            db.session.add(new_bus)
            db.session.commit()

            txns.record_transaction(
                bus_number=bus_number,
                bus_type=bus_type,
                entry_time=entry_time,
                exit_time=entry_time,
                pass_type="None",
                recorded_by=current_user()["username"],
                receipt_number=receipt,
                driver_phone=driver_phone,
                fixed_fee=100,
            )

            return redirect(url_for("receipt", receipt_number=receipt))
    return render_template("bus_entry.html", message=message, msg_type=msg_type, user=current_user())


# ---------------------------
# Receipt View
# ---------------------------
@app.route("/receipt/<receipt_number>")
@login_required
def receipt(receipt_number):
    txn = txns.get_transaction_by_receipt(receipt_number)
    if not txn:
        return render_template("receipt.html", error="Receipt not found.", receipt=None, user=current_user())

    # Try to locate an active parked bus matching this receipt (optional)
    bus = Bus.query.filter_by(receipt_number=receipt_number).first()
    return render_template("receipt.html", txn=txn, bus=bus, user=current_user())


# ---------------------------
# Bus Exit
# ---------------------------
@app.route("/bus_exit", methods=["GET", "POST"])
@login_required
def bus_exit():
    message  = None
    msg_type = "success"
    txn      = None
    if request.method == "POST":
        bus_number     = request.form["bus_number"].strip().upper()
        receipt_number = request.form.get("receipt_number", "").strip().upper()
        bus = Bus.query.filter_by(bus_number=bus_number, status="Parked").first()

        if not bus:
            message  = f"Bus {bus_number} not found in park."
            msg_type = "error"
        elif not receipt_number or receipt_number != (bus.receipt_number or ""):
            message  = "Receipt number does not match. Please provide the correct receipt to exit."
            msg_type = "error"
        else:
            exit_time = datetime.now()
            entry_time = bus.entry_time or exit_time

            txn = txns.record_transaction(
                bus_number=bus_number,
                bus_type=bus.bus_type or "Standard",
                entry_time=entry_time,
                exit_time=exit_time,
                pass_type="None",
                recorded_by=current_user()["username"],
                receipt_number=receipt_number,
                driver_phone=bus.driver_phone,
                fixed_fee=0,
            )
            bus.status = "Exited"
            bus.exit_time = exit_time
            db.session.commit()

            slts.free_slot(bus_number)
            message = (
                f"Bus {bus_number} exited. Receipt {receipt_number} confirmed. "
                f"No additional fee due (payment already made at entry)."
            )
    return render_template("bus_exit.html",
        message=message, msg_type=msg_type, txn=txn,
        user=current_user()
    )


# ---------------------------
# Slots
# ---------------------------
@app.route("/slots")
@login_required
def slots_view():
    total_slots = int(get_setting("total_slots", "100"))
    return render_template("slots.html",
        slots=slts.get_all_slots(),
        total=total_slots,
        available=slts.get_available_count(),
        occupied=slts.get_occupied_count(),
        is_full=slts.is_full(),
        user=current_user()
    )


# ---------------------------
# Transactions
# ---------------------------
@app.route("/transactions")
@login_required
def transactions_view():
    all_txns = txns.get_all_transactions()
    total_revenue   = txns.get_total_revenue()
    total_discount  = round(sum(t["discount_amt"] for t in all_txns), 2)
    return render_template("transactions.html",
        transactions=all_txns,
        total_revenue=total_revenue,
        total_discount=total_discount,
        count=len(all_txns),
        user=current_user()
    )


# ---------------------------
# Reports
# ---------------------------
@app.route("/reports")
@login_required
def reports():
    period = request.args.get("period", "daily")
    if period == "weekly":
        report = rpts.weekly_report()
    elif period == "monthly":
        report = rpts.monthly_report()
    else:
        report = rpts.daily_report()
    return render_template("reports.html",
        report=report,
        period=period,
        occupancy=rpts.occupancy_report(),
        freq_buses=rpts.frequent_buses(),
        freq_drivers=rpts.frequent_drivers(),
        user=current_user()
    )

@app.route("/reports/export")
@login_required
def export_csv():
    csv_data = rpts.export_transactions_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


# ---------------------------
# M-Pesa STK Push
# ---------------------------
@app.route("/mpesa/stk_push", methods=["POST"])
@login_required
def mpesa_stk_push():
    phone       = request.form.get("driver_phone", "").strip()
    amount      = request.form.get("amount", 100)
    account_ref = request.form.get("bus_number", "BUSPARK")
    description = request.form.get("description", "Parking Fee")

    if not phone:
        return jsonify({"success": False, "message": "Phone number is required."})

    result = mpesa.stk_push(
        phone       = phone,
        amount      = amount,
        account_ref = account_ref,
        description = description,
    )
    # include sandbox mode flag in response so UI can show badge
    result["sandbox_mode"] = mpesa.SANDBOX_MODE
    return jsonify(result)


@app.route("/mpesa/query", methods=["POST"])
@login_required
def mpesa_query():
    """Poll payment status for a given CheckoutRequestID."""
    checkout_id = request.form.get("checkout_id", "")
    if not checkout_id:
        return jsonify({"success": False, "message": "Missing checkout ID."})
    result = mpesa.query_stk(checkout_id)
    return jsonify(result)


@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """Daraja callback — receives payment confirmation from Safaricom."""
    data = request.get_json(silent=True) or {}
    print(f"[MPESA CALLBACK] {data}")
    # Extract result
    try:
        body        = data["Body"]["stkCallback"]
        result_code = body["ResultCode"]
        checkout_id = body["CheckoutRequestID"]
        if result_code == 0:
            items = {i["Name"]: i.get("Value") for i in body["CallbackMetadata"]["Item"]}
            amount  = items.get("Amount")
            receipt = items.get("MpesaReceiptNumber")
            phone   = items.get("PhoneNumber")
            print(f"[MPESA] PAID ✅ Receipt:{receipt} Amount:{amount} Phone:{phone} Checkout:{checkout_id}")
        else:
            print(f"[MPESA] FAILED ❌ Code:{result_code} Checkout:{checkout_id}")
    except Exception as e:
        print(f"[MPESA CALLBACK ERROR] {e}")
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


# ---------------------------
# API Endpoints (JSON)
# ---------------------------

@app.route("/api/slots")
@login_required
def api_slots():
    total_slots = int(get_setting("total_slots", "100"))
    return jsonify({
        "slots": slts.get_all_slots(),
        "total": total_slots,
        "available": slts.get_available_count(),
        "occupied": slts.get_occupied_count(),
    })


@app.route("/api/buses")
@login_required
def api_buses():
    buses = [b.to_dict() for b in Bus.query.filter_by(status="Parked").order_by(Bus.entry_time.desc()).all()]
    return jsonify({"buses": buses})


@app.route("/api/transactions")
@login_required
def api_transactions():
    return jsonify({"transactions": txns.get_all_transactions()})


# ---------------------------
# Drivers
# ---------------------------
@app.route("/drivers")
@login_required
def drivers_list():
    return render_template("drivers.html",
        drivers=drv.get_all_drivers(),
        parked_buses=Bus.query.filter_by(status="Parked").all(),
        user=current_user()
    )

@app.route("/drivers/add", methods=["GET", "POST"])
@login_required
def driver_add():
    if request.method == "POST":
        drv.add_driver(
            name=request.form["name"],
            role=request.form["role"],
            phone=request.form["phone"],
            email=request.form["email"],
            license_number=request.form["license_number"],
            assigned_bus=request.form.get("assigned_bus", "")
        )
        return redirect(url_for("drivers_list"))
    return render_template("driver_form.html", action="Add", driver=None,
                           parked_buses=Bus.query.filter_by(status="Parked").all(), message=None, user=current_user())

@app.route("/drivers/edit/<int:driver_id>", methods=["GET", "POST"])
@login_required
def driver_edit(driver_id):
    driver = drv.get_driver_by_id(driver_id)
    if not driver:
        return redirect(url_for("drivers_list"))
    if request.method == "POST":
        drv.edit_driver(driver_id,
            name=request.form["name"], role=request.form["role"],
            phone=request.form["phone"], email=request.form["email"],
            license_number=request.form["license_number"],
            assigned_bus=request.form.get("assigned_bus", "")
        )
        return redirect(url_for("drivers_list"))
    return render_template("driver_form.html", action="Edit", driver=driver,
                           parked_buses=Bus.query.filter_by(status="Parked").all(), message=None, user=current_user())

@app.route("/drivers/delete/<int:driver_id>", methods=["POST"])
@login_required
def driver_delete(driver_id):
    drv.delete_driver(driver_id)
    return redirect(url_for("drivers_list"))

@app.route("/drivers/assign/<int:driver_id>", methods=["POST"])
@login_required
def driver_assign(driver_id):
    drv.assign_bus(driver_id, request.form.get("bus_number", ""))
    return redirect(url_for("drivers_list"))


# ---------------------------
# Users (Admin only)
# ---------------------------
@app.route("/users")
@login_required
def users_list():
    if current_user()["role"] != "Admin":
        return redirect(url_for("home"))
    return render_template("users.html",
        users=usr.get_all_users(), user=current_user(), message=None)

@app.route("/users/add", methods=["POST"])
@login_required
def user_add():
    if current_user()["role"] != "Admin":
        return redirect(url_for("home"))
    success = usr.add_user(
        username=request.form["username"],
        password=request.form["password"],
        role=request.form["role"],
        name=request.form["name"]
    )
    msg = "User added." if success else "Username already exists."
    return render_template("users.html",
        users=usr.get_all_users(), user=current_user(), message=msg)

@app.route("/users/reset", methods=["POST"])
@login_required
def user_reset():
    if current_user()["role"] != "Admin":
        return redirect(url_for("home"))
    usr.reset_password(request.form["username"], request.form["new_password"])
    return render_template("users.html",
        users=usr.get_all_users(), user=current_user(), message="Password reset.")

@app.route("/users/delete/<username>", methods=["POST"])
@login_required
def user_delete(username):
    if current_user()["role"] != "Admin":
        return redirect(url_for("home"))
    usr.delete_user(username)
    return redirect(url_for("users_list"))


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    # Automatically open the browser on localhost when running in dev mode.
    try:
        import webbrowser
        from threading import Timer

        def _open_browser():
            webbrowser.open("http://localhost:5000")

        Timer(1.0, _open_browser).start()
    except Exception:
        pass

    app.run(debug=True)
