import cv2
import json
import time
from pyzbar.pyzbar import decode

# Hardcoded JSON path for crop box
JSON_PATH = "crop_box.json"

def load_crop_box(json_path=JSON_PATH):
    with open(json_path, "r") as f:
        data = json.load(f)
        return data["x"], data["y"], data["width"], data["height"]

def scan_qr_live_cropped_timeout(camera_index=2, timeout_sec=5):
    """
    Scans for a QR code in a cropped region from a live camera feed.
    Crop region is loaded from crop_box.json.
    If no QR code is detected within `timeout_sec` seconds, returns 'b4'.
    Returns:
        str: Decoded QR code data, or 'b4' if not found.
    """
    crop_x, crop_y, crop_width, crop_height = load_crop_box()
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Failed to open camera at index {camera_index}")
        return "b4"

    start_time = time.time()
    qr_data = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        # Draw the virtual box for user alignment
        preview = frame.copy()
        cv2.rectangle(
            preview,
            (crop_x, crop_y),
            (crop_x + crop_width, crop_y + crop_height),
            (0, 255, 0),
            2,
        )
        cv2.imshow("Live Camera (Box Area)", preview)

        # Crop area for QR detection
        cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
        decoded_objects = decode(cropped)
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            print("QR Code detected:", qr_data)
            break

        # Terminate after timeout
        if time.time() - start_time > timeout_sec:
            print(f"No QR code detected in {timeout_sec} seconds.")
            break

        # Optional: allow user to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("User quit program.")
            break

    cap.release()
    cv2.destroyAllWindows()

    # If nothing detected, return 'b4' as default
    return qr_data if qr_data else "b4"