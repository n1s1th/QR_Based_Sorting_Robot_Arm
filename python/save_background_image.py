import cv2

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Previewing camera. Press SPACE to capture and save background image as 'background.jpg'. Press ESC to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        cv2.imshow("Capture Background", frame)
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            cv2.imwrite("background.jpg", frame)
            print("Background image saved as 'background.jpg'.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()