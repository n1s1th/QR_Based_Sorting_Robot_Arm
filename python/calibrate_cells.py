import cv2
import json

rectangles = []
drawing = False
ix, iy = -1, -1
img = None
clone = None
cell_labels = ["A a", "A b", "A c", "B a", "B b", "B c", "C a", "C b", "C c"]  # Change as needed

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, clone, rectangles
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        clone = img.copy()
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img = clone.copy()
            cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
        x0, y0 = min(ix, x), min(iy, y)
        w, h = abs(x - ix), abs(y - iy)
        rectangles.append({"label": cell_labels[len(rectangles)], "x": x0, "y": y0, "w": w, "h": h})
        print(f"Rectangle for {cell_labels[len(rectangles)-1]}: x={x0}, y={y0}, w={w}, h={h}")

def main():
    global img, clone
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open camera.")
        return

    print("Draw rectangles for each cell using mouse.")
    print("Press 's' to save rectangles to JSON. Press 'q' to quit.")

    ret, img = cap.read()
    if not ret:
        print("Could not grab frame.")
        return
    clone = img.copy()
    cv2.namedWindow("Calibrate")
    cv2.setMouseCallback("Calibrate", draw_rectangle)

    while True:
        cv2.imshow("Calibrate", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('s'):
            filename = "tray_cells.json"
            with open(filename, "w") as f:
                json.dump(rectangles, f, indent=2)
            print(f"Saved {len(rectangles)} rectangles to {filename}.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()