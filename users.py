# users.py
# Handles staff/admin login, role-based access, and password reset

import data

ROLE_PERMISSIONS = {
    "Admin": ["home", "bus_entry", "bus_exit", "slots", "drivers",
              "transactions", "reports", "users"],
    "Staff": ["home", "bus_entry", "bus_exit", "slots", "drivers",
              "transactions", "reports"],
}


def login(username, password):
    """Validate credentials. Returns user dict or None."""
    user = data.users.get(username)
    if user and user["password"] == password:
        data.logged_in_user["username"] = username
        data.logged_in_user["role"] = user["role"]
        data.logged_in_user["name"] = user["name"]
        return user
    return None


def logout():
    data.logged_in_user.update({"username": None, "role": None, "name": None})


def get_current_user():
    return data.logged_in_user if data.logged_in_user["username"] else None


def is_logged_in():
    return data.logged_in_user["username"] is not None


def has_permission(page):
    role = data.logged_in_user.get("role")
    return page in ROLE_PERMISSIONS.get(role, [])


def reset_password(username, new_password):
    """Admin-only: reset a user's password."""
    if username in data.users:
        data.users[username]["password"] = new_password
        data.save_data()
        return True
    return False


def get_all_users():
    return [
        {"username": u, "role": v["role"], "name": v["name"]}
        for u, v in data.users.items()
    ]


def add_user(username, password, role, name):
    if username in data.users:
        return False
    data.users[username] = {"password": password, "role": role, "name": name}
    data.save_data()
    return True


def delete_user(username):
    if username in data.users and username != "admin":
        del data.users[username]
        data.save_data()
        return True
    return False
