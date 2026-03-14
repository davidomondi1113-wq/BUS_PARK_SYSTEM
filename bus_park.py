# Bus Park System - Simple Version (Console Mode)

import sys
import os

# Step 1: Initialize bus list
parked_buses = []

# Helper functions

def safe_input(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nNo input provided. Exiting.")
        sys.exit(0)


def print_menu():
    print("\n=== BUS PARK SYSTEM ===")
    print("1. Bus Entry")
    print("2. Bus Exit")
    print("3. Show Parked Buses")
    print("4. Exit Program")
    print("5. Launch Web UI (localhost:5000)")


def run_console_mode():
    while True:
        print_menu()
        choice = safe_input("Enter your choice (1-5): ")

        # Bus Entry
        if choice == "1":
            bus_number = safe_input("Enter bus number: ")
            parked_buses.append(bus_number)
            print(f"Bus {bus_number} entered the park.")

        # Bus Exit
        elif choice == "2":
            bus_number = safe_input("Enter bus number leaving: ")
            if bus_number in parked_buses:
                fee = 200  # Flat fee example
                print(f"Bus {bus_number} has to pay Ksh {fee}.")
                parked_buses.remove(bus_number)
                print(f"Bus {bus_number} exited the park.")
            else:
                print(f"Bus {bus_number} not found in the park!")

        # Show Parked Buses
        elif choice == "3":
            if parked_buses:
                print("Currently parked buses:")
                for bus in parked_buses:
                    print("-", bus)
            else:
                print("No buses in the park.")

        # Exit Program
        elif choice == "4":
            print("Exiting Bus Park System. Goodbye!")
            break

        # Launch Web UI
        elif choice == "5":
            print("Launching web UI (may take a moment)...")
            run_web_mode()
            break

        else:
            print("Invalid choice. Please select 1-5.")


def run_web_mode():
    # Launch the Flask app (main.py)
    os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "main.py")}"')


if __name__ == "__main__":
    # If user passes --web or --serve, start the web UI directly
    if "--web" in sys.argv or "--serve" in sys.argv:
        run_web_mode()
    else:
        run_console_mode()
