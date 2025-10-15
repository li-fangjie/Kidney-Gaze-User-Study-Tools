import cv2
import time
from datetime import datetime
import csv
import argparse


def getAvailableResolutions(videoCapture):
    if not videoCapture.isOpened():
        print("Error: Video source is not open")
        return None

    maxWidth, maxHeight = 0, 0
    availableResolutions = []

    # Test a range of common resolutions (expandable)
    testWidths = [640, 1280, 1920]  # [320, 640, 1280, 1920, 2560, 3840]
    testHeights = [360, 720, 1080]  # [240, 360, 720, 1080, 1440, 2160]

    for width, height in zip(testWidths, testHeights):
        videoCapture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        videoCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        actualWidth = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actualHeight = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if (actualWidth, actualHeight) == (width, height):
            availableResolutions.append((width, height))

            # Track the highest resolution
            if actualWidth * actualHeight > maxWidth * maxHeight:
                maxWidth, maxHeight = actualWidth, actualHeight

    return availableResolutions, (maxWidth, maxHeight)


def time_since_epoch_millisec():
    return int(round(time.time() * 1000))


def main():
    parser = argparse.ArgumentParser(
        description="Script for Saving Videos\
            \nUsage: python script.py <fps> \
            <output_filename> (<width> <height>)"
        )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="The frame rate of the saved video"
        )
    parser.add_argument(
        "--output_filename",
        type=str,
        default="video",
        help="File name stem (time stamp will be appended)")
    parser.add_argument(
        "--input_device_index",
        type=int,
        default=1,
        help="index input source.")
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Width of input source. If left empty, \
            the largest will be picked automatically")
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Height of input source. If left empty, \
            the largest will be picked automatically")

    args = parser.parse_args()

    fps = args.fps  # int(sys.argv[1])
    output_filename = args.output_filename  # sys.argv[2]
    frame_width = args.width
    frame_height = args.height
    input_device_index = args.input_device_index

    curT = datetime.now()
    tString = curT.strftime("%Y%m%d_%H%M%S")

    output_filename += ("_" + tString)

    # Create a VideoCapture object and use camera to capture the video
    cap = cv2.VideoCapture(input_device_index)
    if not cap.isOpened():
        print("Error opening video stream")
        return

    availableRes, bestRes = getAvailableResolutions(cap)
    print(availableRes)

    if (frame_width, frame_height) not in availableRes:
        print(f"frame width or height ({frame_width}, {frame_height})\
 not provided/available, automatically picking the largest size")
        frame_width = bestRes[0]
        frame_height = bestRes[1]
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    # Get frame dimensions
    frame_width_act = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height_act = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    assert(frame_width == frame_width_act)
    assert(frame_height == frame_height_act)

    print(f"Resolution selected: {frame_width} x {frame_height}")
    
    frame_no = 0
    record = False
    old_time = 0
    fps_counter = 0

    # Open a CSV file to store timestamps
    with open(f"{output_filename}.csv", "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Define the codec and create VideoWriter object
        video_writer = cv2.VideoWriter(
            f"{output_filename}.avi",
            cv2.VideoWriter_fourcc(*'MJPG'),
            fps,
            (frame_width, frame_height)
            )
        
        while True:
            ret, frame = cap.read()
            # print(frame.shape)
            if not ret:
                break
            
            # Calculate FPS
            new_time = time_since_epoch_millisec()
            if old_time != 0:
                fps_counter = 1000.0 / (new_time - old_time)
            old_time = new_time

            if record:
                # Write the frame into the file
                video_writer.write(frame)
                # Log the frame number and timestamp
                csv_writer.writerow([frame_no, time_since_epoch_millisec()])
                print(f"\rRecording FPS: {fps_counter:.2f}", end="\r")
                frame_no += 1

            else:
                # pass
                # cv2.imshow("Frame", frame)
                print(f"\rFPS: {fps_counter:.2f}", end="\r")

            cv2.imshow("Frame", frame)
            # Display the resulting frame

            # Press ESC to exit, SPACE to start recording
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                break
            if key == 32:  # SPACE key
                record = True
                print("\nRecording started")

    print()
    # Release everything when done
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
