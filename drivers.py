# drivers.py
# Manages drivers and conductors: add, edit, delete, assign to bus, track contacts

import data
_next_id = 1


def _new_id():
    global _next_id
    id_ = _next_id
    _next_id += 1
    return id_


def get_all_drivers():
    return data.drivers


def get_driver_by_id(driver_id):
    for d in data.drivers:
        if d["id"] == driver_id:
            return d
    return None


def add_driver(name, role, phone, email, license_number, assigned_bus=""):
    driver = {
        "id": _new_id(),
        "name": name,
        "role": role,
        "phone": phone,
        "email": email,
        "license_number": license_number,
        "assigned_bus": assigned_bus,
    }
    data.drivers.append(driver)
    data.save_data()
    return driver


def edit_driver(driver_id, name, role, phone, email, license_number, assigned_bus=""):
    driver = get_driver_by_id(driver_id)
    if not driver:
        return None
    driver.update({
        "name": name, "role": role, "phone": phone,
        "email": email, "license_number": license_number,
        "assigned_bus": assigned_bus,
    })
    data.save_data()
    return driver


def delete_driver(driver_id):
    driver = get_driver_by_id(driver_id)
    if driver:
        data.drivers.remove(driver)
        data.save_data()
        return True
    return False


def assign_bus(driver_id, bus_number):
    driver = get_driver_by_id(driver_id)
    if not driver:
        return None
    driver["assigned_bus"] = bus_number
    data.save_data()
    return driver
