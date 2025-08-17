import cv2
import numpy as np

# Define tray cell positions and labels (update with your actual coordinates)
cell_labels = [
    # Row A
    {"label": "A a", "x": 30,  "y": 40,  "w": 80,  "h": 80},
    {"label": "A b", "x": 130, "y": 40,  "w": 80,  "h": 80},
    {"label": "A c", "x": 230, "y": 40,  "w": 80,  "h": 80},
    # Row B
    {"label": "B a", "x": 30,  "y": 140, "w": 80,  "h": 80},
    {"label": "B b", "x": 130, "y": 140, "w": 80,  "h": 80},
    {"label": "B c", "x": 230, "y": 140, "w": 80,  "h": 80},
    # Row C
    {"label": "C a", "x": 30,  "y": 240, "w": 80,  "h": 80},
    {"label": "C b", "x": 130, "y": 240, "w": 80,  "h": 80},
    {"label": "C c", "x": 230, "y": 240, "w": 80,  "h": 80},
]

# Simple detector parameters
MIN_AREA = 900
MAX_AREA = 90000
OTSU_SENSITIVITY = 22

def capture_image(cam_index=2, window_name="Capture (SPACE to save, ESC to exit)"):
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None
    img = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)
        if key == 27:   # ESC
            break
        elif key == 32:  # SPACE
            img = frame.copy()
            print("Image captured.")
            break
    cap.release()
    cv2.destroyAllWindows()
    return img

def calculate_difference_otsu(img, bg_img):
    bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    diff_gray = cv2.absdiff(bg_gray, img_gray)
    diff_blur = cv2.GaussianBlur(diff_gray, (5,5), 0)
    ret, otsu_thresh = cv2.threshold(diff_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if ret < OTSU_SENSITIVITY:
        diff = np.zeros_like(diff_blur)
    else:
        diff = cv2.GaussianBlur(otsu_thresh, (5,5), 0)
    return diff

def identify_valid_contours(contours, height, width):
    valid_indices = []
    for idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        edge_noise = x == 0 or y == 0 or (x + w) == width or (y + h) == height
        if MIN_AREA < area < MAX_AREA and not edge_noise:
            valid_indices.append(idx)
    return valid_indices

def assign_cell(cx, cy, cell_labels):
    for cell in cell_labels:
        x, y, w, h = cell["x"], cell["y"], cell["w"], cell["h"]
        if x <= cx <= x+w and y <= cy <= y+h:
            return cell["label"]
    return None

def main():
    print("Step 1: Capture background image (no object).")
    bg_img = capture_image(window_name="Background Image")
    if bg_img is None:
        print("Background image not captured.")
        return

    print("Step 2: Place object and capture target image.")
    img = capture_image(window_name="Target Image")
    if img is None:
        print("Target image not captured.")
        return

    print("Detecting objects...")
    diff = calculate_difference_otsu(img, bg_img)
    contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = img.shape[:2]
    valid_indices = identify_valid_contours(contours, height, width)
    output_img = img.copy()

    # Draw cell boundaries and labels for visualization
    for cell in cell_labels:
        cv2.rectangle(output_img, (cell["x"], cell["y"]), (cell["x"]+cell["w"], cell["y"]+cell["h"]), (255,0,0), 1)
        cv2.putText(output_img, cell["label"], (cell["x"], cell["y"]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

    # For each detected object, assign cell address
    for idx in valid_indices:
        cnt = contours[idx]
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00']) if M['m00'] != 0 else None
        cy = int(M['m01']/M['m00']) if M['m00'] != 0 else None
        if cx is not None and cy is not None:
            cell_label = assign_cell(cx, cy, cell_labels)
            if cell_label:
                cv2.circle(output_img, (cx, cy), 5, (0,255,0), -1)
                cv2.putText(output_img, cell_label, (cx+10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                print(f"Detected object in cell: {cell_label}")
            else:
                cv2.circle(output_img, (cx, cy), 5, (0,0,255), -1)
                print("Detected object not in any cell!")
        else:
            print("Could not calculate centroid for contour.")

    cv2.imshow("Tray Cell Assignment", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imwrite("tray_cell_assignment_result.jpg", output_img)
    print("Result image saved as tray_cell_assignment_result.jpg")

if __name__ == "__main__":
    main()