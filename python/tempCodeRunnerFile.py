import cv2
from pyzbar.pyzbar import decode

cap = cv2.VideoCapture(0)

# --- Set your desired scanning area here ---
# Example: top-left corner at (100, 200), area size 200x200 pixels
x1, y1 = 270, 250
scan_width, scan_height = 250, 250

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Ensure ROI stays within frame boundaries
    height, width, _ = frame.shape
    x2 = min(x1 + scan_width, width)
    y2 = min(y1 + scan_height, height)
    x1_ = max(x1, 0)
    y1_ = max(y1, 0)

    # Crop the scanning area
    roi = frame[y1_:y2, x1_:x2]

    # Decode only the cropped area
    decoded_objects = decode(roi)
    for obj in decoded_objects:
        print("Data:", obj.data.decode("utf-8"))

    # Draw rectangle to visualize the scan area
    cv2.rectangle(frame, (x1_, y1_), (x2, y2), (0, 255, 0), 2)
    cv2.imshow('QR Scanner', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
