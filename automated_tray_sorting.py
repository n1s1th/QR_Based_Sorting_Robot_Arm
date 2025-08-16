import cv2
from pyzbar.pyzbar import decode

def scan_qr_from_custom_crop(crop_x, crop_y, crop_width, crop_height, camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture image.")
        return None

    h, w = frame.shape[:2]
    crop_x = max(0, min(crop_x, w - crop_width))
    crop_y = max(0, min(crop_y, h - crop_height))
    crop_width = min(crop_width, w - crop_x)
    crop_height = min(crop_height, h - crop_y)

    cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    decoded_objects = decode(cropped)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")
    return None

def automated_tray_sorting(serial_conn, tray_counts, tray_file, crop_x, crop_y, crop_width, crop_height, camera_index=0):
    """
    Triggers QR scan after 'READY_TO_SCAN', sends tray code to Arduino, updates counts/logs.
    """
    # 1. Trigger QR scan for tray code
    print("Scanning QR code for tray number...")
    tray_code = scan_qr_from_custom_crop(crop_x, crop_y, crop_width, crop_height, camera_index)
    if tray_code not in ['b1', 'b2', 'b3', 'b4']:
        print(f"Invalid or no tray code detected in QR. Detected: {tray_code}")
        return

    print(f"Detected tray code: {tray_code}")

    # 2. Send tray code to Arduino
    serial_conn.write((tray_code + '\n').encode())
    print(f"Sent to Arduino: {tray_code}")

    # 3. Wait for ROUND_COMPLETE from Arduino
    while True:
        if serial_conn.in_waiting:
            response = serial_conn.readline().decode('utf-8').strip()
            print(f"Arduino: {response}")
            if "ROUND_COMPLETE" in response:
                break

    # 4. Update counts and log to file
    tray_counts[tray_code] += 1
    with open(tray_file, "w") as f:
        for key in ["b1", "b2", "b3", "b4"]:
            f.write(f"{key.upper()} count: {tray_counts[key]}\n")

    print(f"\nTray counts so far:")
    for key in ["b1", "b2", "b3", "b4"]:
        print(f"{key.upper()} count: {tray_counts[key]}")
    print("\nStarting next round...\n")