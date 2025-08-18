import cv2

def draw_crop_area_with_mouse(camera_index=2):
    """
    Allows user to draw a crop rectangle with mouse on live camera feed.
    After drawing, prints crop_x, crop_y, crop_width, crop_height to terminal.
    Returns: (crop_x, crop_y, crop_width, crop_height)
    """
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture from camera.")
        cap.release()
        return None

    drawing = False
    ix, iy = -1, -1
    fx, fy = -1, -1
    rect_done = False

    def draw_rectangle(event, x, y, flags, param):
        nonlocal ix, iy, fx, fy, drawing, rect_done
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
            rect_done = True

    cv2.namedWindow('Draw Crop Area')
    cv2.setMouseCallback('Draw Crop Area', draw_rectangle)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        temp_frame = frame.copy()
        if drawing or rect_done:
            cv2.rectangle(temp_frame, (ix, iy), (fx, fy), (0, 255, 0), 2)
        cv2.imshow('Draw Crop Area', temp_frame)
        key = cv2.waitKey(1) & 0xFF
        if rect_done or key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Normalize coordinates
    x1, y1 = min(ix, fx), min(iy, fy)
    x2, y2 = max(ix, fx), max(iy, fy)
    crop_x, crop_y = x1, y1
    crop_width, crop_height = x2 - x1, y2 - y1

    print(f"crop_x = {crop_x}")
    print(f"crop_y = {crop_y}")
    print(f"crop_width = {crop_width}")
    print(f"crop_height = {crop_height}")

    return crop_x, crop_y, crop_width, crop_height

# Example usage:
if __name__ == "__main__":
    draw_crop_area_with_mouse()