# users.py
# Handles staff/admin login, role-based access, and password reset

from database import db
from models import User

ROLE_PERMISSIONS = {
    "Admin": ["home", "bus_entry", "bus_exit", "slots", "drivers",
              "transactions", "reports", "users"],
    "Staff": ["home", "bus_entry", "bus_exit", "slots", "drivers",
              "transactions", "reports"],
}


def login(username, password):
    """Validate credentials. Returns user dict or None."""
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return user.to_dict()
    return None


def reset_password(username, new_password):
    """Admin-only: reset a user's password."""
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = new_password
        db.session.commit()
        return True
    return False


def get_all_users():
    return [u.to_dict() for u in User.query.order_by(User.username).all()]


def add_user(username, password, role, name):
    if User.query.filter_by(username=username).first():
        return False
    user = User(username=username, password=password, role=role, name=name)
    db.session.add(user)
    db.session.commit()
    return True


def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user and user.username != "admin":
        db.session.delete(user)
        db.session.commit()
        return True
    return False
