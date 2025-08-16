import cv2

# Instructions:
# 1. Show your tray under the camera.
# 2. Run this script.
# 3. Use the mouse to draw a rectangle for each cell (click-drag-release).
# 4. Press 's' to save and print all rectangles. Press 'q' to quit.

rectangles = []
drawing = False
ix, iy = -1, -1
img = None
clone = None

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
        # Standardize rectangle: top-left corner, width, height
        x0, y0 = min(ix, x), min(iy, y)
        w, h = abs(x - ix), abs(y - iy)
        rectangles.append((x0, y0, w, h))
        print(f"Rectangle: x={x0}, y={y0}, w={w}, h={h}")

def main():
    global img, clone
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        print("Could not open camera.")
        return

    print("Draw rectangles for each cell using mouse.")
    print("Press 's' to print all rectangles. Press 'q' to quit.")

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
            print("\n--- All rectangles ---")
            for i, rect in enumerate(rectangles):
                print(f"Cell {i+1}: x={rect[0]}, y={rect[1]}, w={rect[2]}, h={rect[3]}")
            print("---------------------")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()