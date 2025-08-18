import serial
import time
from automated_tray_sorting import scan_qr_live_cropped_timeout
from automated_cell_selection import select_random_cell_and_format
import random

def main_controller(
    serial_port='COM6',
    baud_rate=9600,
    tray_file='tray_counts.txt',
    crop_width = 250,
    crop_height = 250,
    crop_x = 250,
    crop_y = 200,
    camera_index = 2):

    tray_counts = {"b1": 0, "b2": 0, "b3": 0, "b4": 0}

    # Load previous tray counts if file exists
    try:
        with open(tray_file, "r") as f:
            for line in f:
                if "count:" in line:
                    key, count = line.strip().split(" count:")
                    key = key.lower()
                    if key in tray_counts:
                        tray_counts[key] = int(count)
    except FileNotFoundError:
        pass

    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)

    print("Connected to Arduino on", serial_port)

    while True:
        # ---- 1. Wait for Arduino prompt for slider/arm action ----
        print("\nWaiting for Arduino to request slider/arm input...")
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                print("Arduino:", line)
                if "slider position" in line:
                    break

        # ---- 2. Automated cell selection instead of manual entry ----
        cell_label = select_random_cell_and_format()
        if cell_label is None:
            print("No cell detected, skipping this round or defaulting to a value.")
            continue

        # Optionally, automate arm action as well
        arm_actions = ['a', 'b', 'c', 'd']
        arm = random.choice(arm_actions)
        print(f"Automated selection: Slider cell '{cell_label}', Arm '{arm}'")

        user_input = f"{cell_label} {arm}"

        # ---- 3. Send slider/arm input to Arduino ----
        ser.write((user_input + '\n').encode())
        print("Sent to Arduino:", user_input)

        # ---- 4. Wait for READY_TO_SCAN from Arduino ----
        print("Waiting for Arduino to signal READY_TO_SCAN...")
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                print("Arduino:", line)
                if "READY_TO_SCAN" in line:
                    break

        # ---- 5. Scan QR code for tray selection using new method ----
        print("Scanning QR code for tray number (live, 5s timeout)...")
        tray_code = scan_qr_live_cropped_timeout(camera_index=camera_index, timeout_sec=5)
        if tray_code not in ['b1', 'b2', 'b3', 'b4']:
            print("No valid QR code detected. Defaulting to tray 'b4'.")
            tray_code = 'b4'
        else:
            print(f"Detected tray code: {tray_code}")

        ser.write((tray_code + '\n').encode())
        print(f"Sent to Arduino: {tray_code}")

        # ---- 6. Wait for ROUND_COMPLETE from Arduino ----
        print("Waiting for Arduino to signal ROUND_COMPLETE...")
        while True:
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                print("Arduino:", response)
                if "ROUND_COMPLETE" in response:
                    break

        # ---- 7. Update counts and log to file ----
        tray_counts[tray_code] += 1
        with open(tray_file, "w") as f:
            for key in ["b1", "b2", "b3", "b4"]:
                f.write(f"{key.upper()} count: {tray_counts[key]}\n")

        print(f"\nTray counts so far:")
        for key in ["b1", "b2", "b3", "b4"]:
            print(f"{key.upper()} count: {tray_counts[key]}")
        print("\nRound complete. Ready for next round!\n")

if __name__ == "__main__":
    main_controller()   