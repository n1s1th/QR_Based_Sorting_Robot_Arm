import serial
import time
from automated_tray_sorting import scan_qr_live_cropped_timeout
from automated_cell_selection import select_random_cell_and_format
import random
import threading

TRAY_FILE = 'tray_counts.txt'
LOG_FILE = 'system.log'
TRAYS = ["b1", "b2", "b3", "b4"]

def log_message(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

def main_controller(
    serial_port='COM6',
    baud_rate=9600,
    tray_file=TRAY_FILE,
    camera_index=2):

    tray_counts = {tray: 0 for tray in TRAYS}

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

    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)
        log_message(f"Connected to Arduino on {serial_port}")
    except Exception as e:
        log_message(f"Serial connection error: {e}")
        return

    while True:
        # 1. Stop if any tray is full
        full_trays = [tray for tray, count in tray_counts.items() if count >= 4]
        if full_trays:
            log_message(f"Tray(s) full: {', '.join(full_trays)}. System stopped. Please reset.")
            break

        # 2. Wait for Arduino prompt for slider/arm action
        log_message("Waiting for Arduino to request slider/arm input...")
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {line}")
                if "slider position" in line:
                    break

        # 3. Automated cell selection, check for empty tray
        cell_label = select_random_cell_and_format()
        retry_count = 0
        while cell_label is None:
            log_message("No object detected in tray. Retrying in 10 seconds...")
            time.sleep(10)
            cell_label = select_random_cell_and_format()
            retry_count += 1
            if retry_count >= 12:  # Optional: Give up after 2 minutes
                log_message("No object detected after multiple retries. System stopped.")
                return

        # 4. Random arm action
        arm_actions = ['a', 'b', 'c', 'd']
        arm = random.choice(arm_actions)
        log_message(f"Automated selection: Slider cell '{cell_label}', Arm '{arm}'")
        user_input = f"{cell_label} {arm}"

        # 5. Send slider/arm input to Arduino
        ser.write((user_input + '\n').encode())
        log_message(f"Sent to Arduino: {user_input}")

        # 6. Wait for READY_TO_SCAN from Arduino
        log_message("Waiting for Arduino to signal READY_TO_SCAN...")
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {line}")
                if "READY_TO_SCAN" in line:
                    break

        # 7. Scan QR code for tray selection (5s timeout)
        log_message("Scanning QR code for tray number (live, 5s timeout)...")
        tray_code = scan_qr_live_cropped_timeout(camera_index=camera_index, timeout_sec=5)
        if tray_code not in TRAYS:
            log_message("No valid QR code detected. Defaulting to tray 'b4'.")
            tray_code = 'b4'
        else:
            log_message(f"Detected tray code: {tray_code}")

        ser.write((tray_code + '\n').encode())
        log_message(f"Sent to Arduino: {tray_code}")

        # 8. Wait for ROUND_COMPLETE from Arduino
        log_message("Waiting for Arduino to signal ROUND_COMPLETE...")
        while True:
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {response}")
                if "ROUND_COMPLETE" in response:
                    break

        # 9. Update counts and log to file
        tray_counts[tray_code] += 1
        with open(tray_file, "w") as f:
            for key in TRAYS:
                f.write(f"{key.upper()} count: {tray_counts[key]}\n")

        log_message("Tray counts so far:")
        for key in TRAYS:
            log_message(f"{key.upper()} count: {tray_counts[key]}")
        log_message("Round complete. Ready for next round!\n")

if __name__ == "__main__":
    main_controller()