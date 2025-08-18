import cv2
from pyzbar.pyzbar import decode

def scan_qr_live_cropped(crop_x, crop_y, crop_width, crop_height, camera_index=0):
    """
    Scans for a QR code in a cropped region from a live camera feed.
    Returns the first detected QR code data and exits.

    Args:
        crop_x (int): X coordinate of the top-left corner of the crop area.
        crop_y (int): Y coordinate of the top-left corner of the crop area.
        crop_width (int): Width of the crop area.
        crop_height (int): Height of the crop area.
        camera_index (int): Index of the camera (default: 0).

    Returns:
        str or None: Decoded QR code data, or None if not found.
    """
    cap = cv2.VideoCapture(camera_index)
    qr_data = None

    while True:
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
            break

        # Optional: Show the live cropped area for alignment
        preview = frame.copy()
        cv2.rectangle(preview, (crop_x, crop_y), (crop_x + crop_width, crop_y + crop_height), (0, 255, 0), 2)
        cv2.imshow('Live QR Crop (press Q to quit)', preview)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return qr_data

# Example usage:
if __name__ == "__main__":
    crop_x = 105
    crop_y = 101
    crop_width = 161
    crop_height = 175
    data = scan_qr_live_cropped(crop_x, crop_y, crop_width, crop_height)
    print("QR code data:" if data else "No QR code detected.", data)
