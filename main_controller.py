import serial
import time
import cv2
from pyzbar.pyzbar import decode

# -------- QR SCANNING FUNCTION --------
def scan_qr_from_custom_crop(crop_x, crop_y, crop_width, crop_height, camera_index=0):
    """
    Captures an image from the webcam, crops the region defined by (crop_x, crop_y, crop_width, crop_height),
    scans for a QR code in that region, and returns the decoded data if found.

    Returns:
        str or None: Decoded QR code data, or None if not found.
    """
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture image.")
        return None

    h, w = frame.shape[:2]
    # Ensure crop area is within bounds
    crop_x = max(0, min(crop_x, w - crop_width))
    crop_y = max(0, min(crop_y, h - crop_height))
    crop_width = min(crop_width, w - crop_x)
    crop_height = min(crop_height, h - crop_y)

    cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    decoded_objects = decode(cropped)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")  # Return the data of the first QR code found

    return None  # No QR code found

# -------- MAIN CONTROLLER --------
def main_controller(
    serial_port='COM6',
    baud_rate=9600,
    tray_file='tray_counts.txt',
    crop_x=200, crop_y=400, crop_width=250, crop_height=250, camera_index=0
):
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

        # ---- 2. Prompt user for slider/arm input ----
        while True:
            user_input = input("Enter slider position and arm (e.g. C c): ").strip()
            split_input = user_input.split()
            if len(split_input) == 2:
                slider, arm = split_input
                if slider in ['A', 'B', 'C', 'D'] and arm in ['a', 'b', 'c', 'd']:
                    break
            print("Invalid input. Format: [A-D] [a-d] (case sensitive). Try again.")

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

        # ---- 5. Scan QR code for tray selection ----
        print("Scanning QR code for tray number...")
        attempts = 0
        tray_code = None
        while attempts < 5:
            tray_code = scan_qr_from_custom_crop(crop_x, crop_y, crop_width, crop_height, camera_index)
            if tray_code in ['b1', 'b2', 'b3', 'b4']:
                break
            print(f"Attempt {attempts+1}: No valid QR code found. Retrying...")
            time.sleep(1)
            attempts += 1

        if tray_code not in ['b1', 'b2', 'b3', 'b4']:
            print("Failed to detect valid tray QR code after 5 attempts. Skipping this round.")
            continue

        print(f"Detected tray code: {tray_code}")

        # ---- 6. Send tray code to Arduino ----
        ser.write((tray_code + '\n').encode())
        print(f"Sent to Arduino: {tray_code}")

        # ---- 7. Wait for ROUND_COMPLETE from Arduino ----
        print("Waiting for Arduino to signal ROUND_COMPLETE...")
        while True:
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                print("Arduino:", response)
                if "ROUND_COMPLETE" in response:
                    break

        # ---- 8. Update counts and log to file ----
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