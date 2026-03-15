from datetime import datetime

from database import db


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.String(1024), nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="Staff")
    name = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"username": self.username, "role": self.role, "name": self.name}


class Slot(db.Model):
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.Integer, unique=True, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="available")
    bus_number = db.Column(db.String(64), nullable=True)

    def to_dict(self):
        return {"slot_number": self.slot_number, "status": self.status, "bus_number": self.bus_number}


class Bus(db.Model):
    __tablename__ = "buses"

    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(64), unique=True, nullable=False)
    bus_type = db.Column(db.String(64), nullable=False, default="Standard")
    route = db.Column(db.String(128), nullable=True)
    owner = db.Column(db.String(128), nullable=True)
    slot_number = db.Column(db.Integer, nullable=True)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="Parked")
    receipt_number = db.Column(db.String(128), nullable=True)
    driver_phone = db.Column(db.String(64), nullable=True)

    def to_dict(self):
        return {
            "bus_number": self.bus_number,
            "bus_type": self.bus_type,
            "route": self.route,
            "owner": self.owner,
            "slot": self.slot_number,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "status": self.status,
            "receipt_number": self.receipt_number,
            "driver_phone": self.driver_phone,
        }


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    license_number = db.Column(db.String(64), nullable=True)
    assigned_bus = db.Column(db.String(64), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "phone": self.phone,
            "email": self.email,
            "license_number": self.license_number,
            "assigned_bus": self.assigned_bus,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(64), nullable=False)
    bus_type = db.Column(db.String(64), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    gross_fee = db.Column(db.Float, nullable=False)
    discount_pct = db.Column(db.Float, nullable=False)
    discount_amt = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    pass_used = db.Column(db.String(64), nullable=False)
    recorded_by = db.Column(db.String(128), nullable=False)
    receipt_number = db.Column(db.String(128), nullable=True)
    driver_phone = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bus_number": self.bus_number,
            "bus_type": self.bus_type,
            "entry_time": self.entry_time.strftime("%Y-%m-%d %H:%M"),
            "exit_time": self.exit_time.strftime("%Y-%m-%d %H:%M"),
            "duration_minutes": self.duration_minutes,
            "gross_fee": self.gross_fee,
            "discount_pct": self.discount_pct,
            "discount_amt": self.discount_amt,
            "amount_paid": self.amount_paid,
            "pass_used": self.pass_used,
            "recorded_by": self.recorded_by,
            "receipt_number": self.receipt_number,
            "driver_phone": self.driver_phone,
            "date": self.exit_time.strftime("%Y-%m-%d"),
        }
