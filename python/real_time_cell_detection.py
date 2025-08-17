import cv2
import numpy as np
import json

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

def main():
    cell_labels = load_cell_labels("tray_cells.json")
    bg_img = cv2.imread("background.jpg")
    if bg_img is None:
        print("Error: 'background.jpg' not found. Run save_background_image.py first.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Real-time cell detection started. Press ESC to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        diff = calculate_difference_otsu(frame, bg_img)
        contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        height, width = frame.shape[:2]
        valid_indices = identify_valid_contours(contours, height, width)
        output_img = frame.copy()

        # Draw cell boundaries and labels
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
                else:
                    cv2.circle(output_img, (cx, cy), 5, (0,0,255), -1)

        cv2.imshow("Real-Time Cell Detection", output_img)
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()