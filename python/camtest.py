import cv2
from pyzbar.pyzbar import decode

def scan_qr_code(image):
    """
    Scans QR codes from the given image and prints their type and data.
    Returns a list of decoded objects.
    """
    decoded_objects = decode(image)
    for obj in decoded_objects:
        print("Type:", obj.type)
        print("Data:", obj.data.decode("utf-8"))
    return decoded_objects

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# --- Set your desired scanning area's top-left corner and size ---
# Example: scan area at (x1=100, y1=150), size 200x200 px
x1, y1 = 100, 150
scan_width, scan_height = 200, 200

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Ensure ROI is within the frame boundaries
    x2 = min(x1 + scan_width, 640)
    y2 = min(y1 + scan_height, 480)
    x1_ = max(x1, 0)
    y1_ = max(y1, 0)

    # Crop the scanning area
    roi = frame[y1_:y2, x1_:x2]

    # Scan QR code in the specific region
    scan_qr_code(roi)

    # Draw rectangle to show the scanning area
    cv2.rectangle(frame, (x1_, y1_), (x2, y2), (0, 255, 0), 2)
    cv2.imshow('QR Scanner (640x480, Specific Area)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()