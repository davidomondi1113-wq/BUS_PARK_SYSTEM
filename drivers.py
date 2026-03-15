# drivers.py
# Manages drivers and conductors using the database

from database import db
from models import Driver


def get_all_drivers():
    return [d.to_dict() for d in Driver.query.order_by(Driver.name).all()]


def get_driver_by_id(driver_id):
    driver = Driver.query.get(driver_id)
    return driver.to_dict() if driver else None


def add_driver(name, role, phone, email, license_number, assigned_bus=""):
    driver = Driver(
        name=name,
        role=role,
        phone=phone,
        email=email,
        license_number=license_number,
        assigned_bus=assigned_bus,
    )
    db.session.add(driver)
    db.session.commit()
    return driver.to_dict()


def edit_driver(driver_id, name, role, phone, email, license_number, assigned_bus=""):
    driver = Driver.query.get(driver_id)
    if not driver:
        return None
    driver.name = name
    driver.role = role
    driver.phone = phone
    driver.email = email
    driver.license_number = license_number
    driver.assigned_bus = assigned_bus
    db.session.commit()
    return driver.to_dict()


def delete_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if driver:
        db.session.delete(driver)
        db.session.commit()
        return True
    return False


def assign_bus(driver_id, bus_number):
    driver = Driver.query.get(driver_id)
    if not driver:
        return None
    driver.assigned_bus = bus_number
    db.session.commit()
    return driver.to_dict()
