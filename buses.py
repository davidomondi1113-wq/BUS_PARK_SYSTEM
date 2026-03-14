# buses.py

# -----------------------------
# In-Memory Data Storage
# -----------------------------
parked_buses = []  # List of dictionaries: each bus info
parking_slots = {}  # key=slot number, value=bus_number or None
TOTAL_SLOTS = 100  # Max parking slots

# Initialize all slots as free
for i in range(1, TOTAL_SLOTS + 1):
    parking_slots[i] = None

# -----------------------------
# Add a new bus
# -----------------------------
def add_bus(bus_number, bus_type='Unknown', route='Unknown', owner='Unknown'):
    # Check if bus already exists
    if any(bus['bus_number'] == bus_number for bus in parked_buses):
        return False, f"Bus {bus_number} already exists."
    
    # Assign first available parking slot
    available_slot = None
    for slot, b_number in parking_slots.items():
        if b_number is None:
            available_slot = slot
            break
    if available_slot is None:
        return False, "No available parking slots."

    # Create bus record
    bus_info = {
        "bus_number": bus_number,
        "bus_type": bus_type,
        "route": route,
        "owner": owner,
        "slot": available_slot,
        "status": "Parked"  # or "Exited"
    }
    parked_buses.append(bus_info)
    parking_slots[available_slot] = bus_number
    return True, f"Bus {bus_number} added and assigned to slot {available_slot}."

# -----------------------------
# Edit existing bus
# -----------------------------
def edit_bus(bus_number, **kwargs):
    for bus in parked_buses:
        if bus['bus_number'] == bus_number:
            for key, value in kwargs.items():
                if key in bus:
                    bus[key] = value
            return True, f"Bus {bus_number} updated successfully."
    return False, f"Bus {bus_number} not found."

# -----------------------------
# Delete a bus
# -----------------------------
def delete_bus(bus_number):
    for bus in parked_buses:
        if bus['bus_number'] == bus_number:
            slot = bus.get('slot')
            if slot:
                parking_slots[slot] = None  # Free the slot
            parked_buses.remove(bus)
            return True, f"Bus {bus_number} deleted successfully."
    return False, f"Bus {bus_number} not found."

# -----------------------------
# Bus Exit
# -----------------------------
def bus_exit(bus_number):
    for bus in parked_buses:
        if bus['bus_number'] == bus_number and bus['status'] == "Parked":
            bus['status'] = "Exited"
            slot = bus.get('slot')
            if slot:
                parking_slots[slot] = None  # Free slot
            # Flat parking fee (collected at entry in the web UI)
            fee_paid = 100
            return True, f"Bus {bus_number} exited successfully. Fee: Ksh {fee_paid}", fee_paid
    return False, f"Bus {bus_number} not found or already exited.", 0

# -----------------------------
# Track all parked buses
# -----------------------------
def get_parked_buses():
    return [bus for bus in parked_buses if bus['status'] == "Parked"]

# -----------------------------
# Get all parking slots status
# -----------------------------
def get_parking_slots():
    return parking_slots