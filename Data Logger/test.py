import cv2

# Open the webcam
cap = cv2.VideoCapture(2)

# Test common resolutions
resolutions = [(640, 480), (1280, 720), (1920, 1080), (3840, 2160)]
supported_resolutions = []

for width, height in resolutions:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if actual_width == width and actual_height == height:
        supported_resolutions.append((width, height))

cap.release()

print("Supported Resolutions:")
for resolution in supported_resolutions:
    print(f"{resolution[0]}x{resolution[1]}")