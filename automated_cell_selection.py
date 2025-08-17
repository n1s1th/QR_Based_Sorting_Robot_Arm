import cv2
import numpy as np
import json
import time
import random

MIN_AREA = 900
MAX_AREA = 90000
OTSU_SENSITIVITY = 22

def load_cell_labels(filename="tray_cells.json"):
    with open(filename, "r") as f:
        return json.load(f)

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

def select_random_cell_and_format(delay_sec=2):
    cell_labels = load_cell_labels("tray_cells.json")
    bg_img = cv2.imread("background.jpg")
    if bg_img is None:
        print("Error: 'background.jpg' not found. Run save_background_image.py first.")
        return None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    print(f"Waiting {delay_sec} seconds before capturing tray image...")
    for _ in range(10):
        cap.read()
    time.sleep(delay_sec)

    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        cap.release()
        return None

    diff = calculate_difference_otsu(frame, bg_img)
    contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = frame.shape[:2]
    valid_indices = identify_valid_contours(contours, height, width)

    detected_cells = []
    for idx in valid_indices:
        cnt = contours[idx]
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00']) if M['m00'] != 0 else None
        cy = int(M['m01']/M['m00']) if M['m00'] != 0 else None
        if cx is not None and cy is not None:
            cell_label = assign_cell(cx, cy, cell_labels)
            if cell_label:
                detected_cells.append(cell_label)
                print(f"Detected object in cell: {cell_label}")

    cap.release()
    cv2.destroyAllWindows()

    if not detected_cells:
        print("No objects detected in any cell.")
        return None

    selected_cell = random.choice(detected_cells)
    print(f"Randomly selected cell for Arduino: {selected_cell}")

    # You may need to map this label to Arduino format, e.g. ('A', 'b')
    # For now, just return the cell label
    return selected_cell

# If you want to test this module standalone:
if __name__ == "__main__":
    cell = select_random_cell_and_format()
    print("Selected cell:", cell)