import cv2
import numpy as np
import time
import csv
import sys

def time_since_epoch_millisec():
    return int(round(time.time() * 1000))

def main():
    # Check for command line arguments
    if len(sys.argv) < 3:
        print("Usage: python script.py <fps> <output_filename>")
        return

    fps = int(sys.argv[1])
    output_filename = sys.argv[2]

    # Create a VideoCapture object and use camera to capture the video
    cap = cv2.VideoCapture(2)  # Change the index based on your camera
    # print("hi")
    if not cap.isOpened():
        print("Error opening video stream")
        return

    frame_width = 1280
    frame_height = 720

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    # Get frame dimensions
    frame_width_act = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height_act = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    assert(frame_width == frame_width_act)
    assert(frame_height == frame_height)

    print(frame_width)
    print(frame_height)
    
    frame_no = 0
    record = False
    old_time = 0
    fps_counter = 0

    # Open a CSV file to store timestamps
    with open(f"{output_filename}.csv", "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Define the codec and create VideoWriter object
        video_writer = cv2.VideoWriter(f"{output_filename}.avi", 
                                        cv2.VideoWriter_fourcc(*'MJPG'), 
                                        fps, 
                                        (frame_width, frame_height))
        
        while True:
            ret, frame = cap.read()
            print(frame.shape)
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
                print(f"\rRecording FPS: {fps_counter:.2f}", end="")
                frame_no += 1
            else:
                # pass
                print(f"\rFPS: {fps_counter:.2f}", end="")

            # Display the resulting frame
            cv2.imshow("Frame", frame)

            # Press ESC to exit, SPACE to start recording
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                break
            if key == 32:  # SPACE key
                record = True
                print("Recording started")

    # Release everything when done
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    main()