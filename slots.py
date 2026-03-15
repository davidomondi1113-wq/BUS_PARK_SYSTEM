# slots.py
# Tracks parking slot availability using the database

from models import Slot
from database import db


def get_all_slots():
    return [s.to_dict() for s in Slot.query.order_by(Slot.slot_number).all()]


def get_slot_by_number(slot_number):
    slot = Slot.query.filter_by(slot_number=slot_number).first()
    return slot.to_dict() if slot else None


def get_available_count():
    return Slot.query.filter_by(status="available").count()


def get_occupied_count():
    return Slot.query.filter_by(status="occupied").count()


def is_full():
    return get_available_count() == 0


def assign_slot(bus_number):
    slot = Slot.query.filter_by(status="available").order_by(Slot.slot_number).first()
    if not slot:
        return None
    slot.status = "occupied"
    slot.bus_number = bus_number
    db.session.commit()
    return slot.to_dict()


def free_slot(bus_number):
    slot = Slot.query.filter_by(bus_number=bus_number).first()
    if not slot:
        return None
    slot.status = "available"
    slot.bus_number = None
    db.session.commit()
    return slot.to_dict()


def get_slot_for_bus(bus_number):
    slot = Slot.query.filter_by(bus_number=bus_number).first()
    return slot.to_dict() if slot else None
