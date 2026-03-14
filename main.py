# main.py
from flask import Flask, render_template, request, redirect, url_for, session, Response
from datetime import datetime
import uuid
import data
import drivers as drv
import slots as slts
import transactions as txns
import reports as rpts
import users as usr

app = Flask(__name__)
app.secret_key = "kisumu_bus_park_secret"


# ---------------------------
# Setup helpers
# ---------------------------

def ensure_default_user():
    """Ensure there is at least one user (admin) to log in with."""
    if not data.users:
        usr.add_user("admin", "admin123", "Admin", "Administrator")
        print("[INFO] Created default admin user: admin/admin123")


def _generate_receipt_number():
    """Generate a short, unique receipt number for parking payments."""
    return f"R{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


# Ensure a default login exists on startup.
ensure_default_user()


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
    setup_mode = not bool(data.users)

    if setup_mode and request.method == "POST":
        # First-time setup: create the first admin user
        username = request.form.get("username", "admin").strip() or "admin"
        password = request.form.get("password", "admin123")
        name = request.form.get("name", "Administrator").strip() or "Administrator"
        usr.add_user(username, password, "Admin", name)
        return redirect(url_for("login"))

    if request.method == "POST" and not setup_mode:
        user = usr.login(request.form["username"], request.form["password"])
        if user:
            session["user"] = {
                "username": request.form["username"],
                "role": user["role"],
                "name": user["name"],
            }
            return redirect(url_for("home"))
        error = "Invalid username or password."

    return render_template("login.html", error=error, setup=setup_mode)

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
    return render_template("home.html",
        buses=data.parked_buses,
        occupancy=occ,
        total_revenue=txns.get_total_revenue(),
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
        elif any(b["bus_number"] == bus_number for b in data.parked_buses):
            message  = f"Bus {bus_number} is already parked!"
            msg_type = "error"
        elif slts.is_full():
            message  = "⚠️ Park is FULL! No available slots."
            msg_type = "error"
        else:
            receipt = _generate_receipt_number()
            entry_time = datetime.now()
            slot = slts.assign_slot(bus_number)
            data.parked_buses.append({
                "bus_number":     bus_number,
                "bus_type":       bus_type,
                "route":          route,
                "owner":          owner,
                "driver_name":    driver_name,
                "driver_phone":   driver_phone,
                "receipt_number": receipt,
                "slot":           slot["slot_number"],
                "entry_time":     entry_time,
            })

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

            data.save_data()
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
    bus = next((b for b in data.parked_buses if b.get("receipt_number") == receipt_number), None)
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
        bus = next((b for b in data.parked_buses if b["bus_number"] == bus_number), None)

        if not bus:
            message  = f"Bus {bus_number} not found in park."
            msg_type = "error"
        elif not receipt_number or receipt_number != bus.get("receipt_number"):
            message  = "Receipt number does not match. Please provide the correct receipt to exit."
            msg_type = "error"
        else:
            exit_time = datetime.now()
            entry_time = bus.get("entry_time", exit_time)
            if isinstance(entry_time, str):
                try:
                    entry_time = datetime.strptime(entry_time, "%Y-%m-%d %H:%M")
                except Exception:
                    entry_time = exit_time

            txn = txns.record_transaction(
                bus_number=bus_number,
                bus_type=bus.get("bus_type", "Standard"),
                entry_time=entry_time,
                exit_time=exit_time,
                pass_type="None",
                recorded_by=current_user()["username"],
                receipt_number=receipt_number,
                driver_phone=bus.get("driver_phone"),
                fixed_fee=0,
            )
            data.parked_buses.remove(bus)
            slts.free_slot(bus_number)
            data.save_data()
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
    return render_template("slots.html",
        slots=slts.get_all_slots(),
        total=slts.TOTAL_SLOTS,
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
# Drivers
# ---------------------------
@app.route("/drivers")
@login_required
def drivers_list():
    return render_template("drivers.html",
        drivers=drv.get_all_drivers(),
        parked_buses=data.parked_buses,
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
                           parked_buses=data.parked_buses, message=None, user=current_user())

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
                           parked_buses=data.parked_buses, message=None, user=current_user())

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
