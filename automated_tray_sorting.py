import cv2
from pyzbar.pyzbar import decode

def scan_qr_live_cropped(crop_x, crop_y, crop_width, crop_height, camera_index=0, max_attempts=5):
    """
    Scans for a QR code in a cropped region from a live camera feed.
    Tries up to `max_attempts` times. If none found, returns 'b4'.

    Returns:
        str: Decoded QR code data, or 'b4' if not found.
    """
    cap = cv2.VideoCapture(camera_index)
    qr_data = None
    attempts = 0

    while attempts < max_attempts:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame from camera.")
            break

        h, w = frame.shape[:2]
        # Ensure crop area is within bounds
        crop_x = max(0, min(crop_x, w - crop_width))
        crop_y = max(0, min(crop_y, h - crop_height))
        crop_width = min(crop_width, w - crop_x)
        crop_height = min(crop_height, h - crop_y)

        cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]

        decoded_objects = decode(cropped)
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            print(f"QR detected: {qr_data}")
            break

        # Optional: Show preview
        preview = frame.copy()
        cv2.rectangle(preview, (crop_x, crop_y), (crop_x + crop_width, crop_y + crop_height), (0, 255, 0), 2)
        cv2.imshow('Live QR Crop (press Q to quit)', preview)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User quit scanning.")
            break

        print(f"Attempt {attempts+1}: No QR code detected.")
        attempts += 1

    cap.release()
    cv2.destroyAllWindows()

    if qr_data is None:
        print("No QR code detected after max attempts. Returning 'b4'.")
        qr_data = "b4"
    return qr_data