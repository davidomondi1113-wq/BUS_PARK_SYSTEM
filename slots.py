# slots.py
# Tracks parking slot availability: initialize, assign, free, capacity check, full alert

import data

TOTAL_SLOTS = data.TOTAL_SLOTS


def get_all_slots():
    return data.slots


def get_slot_by_number(slot_number):
    for s in data.slots:
        if s["slot_number"] == slot_number:
            return s
    return None


def get_available_count():
    return sum(1 for s in data.slots if s["status"] == "available")


def get_occupied_count():
    return sum(1 for s in data.slots if s["status"] == "occupied")


def is_full():
    return get_available_count() == 0


def assign_slot(bus_number):
    for s in data.slots:
        if s["status"] == "available":
            s["status"] = "occupied"
            s["bus_number"] = bus_number
            data.save_data()
            return s
    return None


def free_slot(bus_number):
    for s in data.slots:
        if s["bus_number"] == bus_number:
            s["status"] = "available"
            s["bus_number"] = None
            data.save_data()
            return s
    return None


def get_slot_for_bus(bus_number):
    for s in data.slots:
        if s["bus_number"] == bus_number:
            return s
    return None
