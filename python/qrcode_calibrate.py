import cv2
import json

def main():
    camera_index = 2
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Failed to open camera at index {camera_index}")
        return

    drawing = False
    ix, iy = -1, -1
    fx, fy = -1, -1
    box_done = False

    def draw_rectangle(event, x, y, flags, param):
        nonlocal ix, iy, fx, fy, drawing, box_done
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
            fx, fy = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                fx, fy = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            fx, fy = x, y
            box_done = True

    cv2.namedWindow("Draw Crop Box")
    cv2.setMouseCallback("Draw Crop Box", draw_rectangle)

    print("Draw a rectangle with mouse to select crop area. Press SPACE to save, Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        temp_frame = frame.copy()
        if drawing or box_done:
            cv2.rectangle(temp_frame, (ix, iy), (fx, fy), (0, 255, 0), 2)
        cv2.imshow("Draw Crop Box", temp_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Quit without saving.")
            break
        elif key == ord(' '):
            if box_done:
                # Normalize coordinates
                x1, y1 = min(ix, fx), min(iy, fy)
                x2, y2 = max(ix, fx), max(iy, fy)
                crop_x, crop_y = x1, y1
                crop_width, crop_height = x2 - x1, y2 - y1

                # Save to JSON
                crop_box = {
                    "x": crop_x,
                    "y": crop_y,
                    "width": crop_width,
                    "height": crop_height
                }
                with open("crop_box.json", "w") as f:
                    json.dump(crop_box, f, indent=2)
                print("Saved crop box to crop_box.json:", crop_box)
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()