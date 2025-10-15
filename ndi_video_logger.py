import cv2
import numpy as np
import time
import threading
import select
import sys
import os
from datetime import datetime
import csv
from sksurgerynditracker.nditracker import NDITracker

# Global variables
stop_threads = False
capture_requested = False
last_captures = []  # Will store tuples of (timestamp, transforms, frame)

def time_since_epoch_millisec():
    return int(round(time.time() * 1000))

def get_available_resolutions(video_capture):
    """Determine available resolutions for the camera"""
    if not video_capture.isOpened():
        print("Error: Video source is not open")
        return None, None

    max_width, max_height = 0, 0
    available_resolutions = []

    # Test common resolutions
    test_widths = [640, 1280, 1920]
    test_heights = [360, 720, 1080]

    for width, height in zip(test_widths, test_heights):
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        actual_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if (actual_width, actual_height) == (width, height):
            available_resolutions.append((width, height))

            # Track the highest resolution
            if actual_width * actual_height > max_width * max_height:
                max_width, max_height = actual_width, actual_height

    return available_resolutions, (max_width, max_height)

def get_transformations(tracker):
    """Fetches all transformation matrices from the Polaris tracker."""
    frame_data = tracker.get_frame()
    
    if isinstance(frame_data, tuple) and len(frame_data) >= 4:
        transformation_matrices = frame_data[3]  # Extract the transformation matrices
        
        if isinstance(transformation_matrices, list):
            # Filter out invalid matrices
            valid_matrices = []
            for matrix in transformation_matrices:
                # if isinstance(matrix, np.ndarray) and matrix.shape == (4, 4) and not np.any(np.isnan(matrix)):
                valid_matrices.append(matrix)
            
            if valid_matrices:
                return valid_matrices
            else:
                print("No valid transformation matrices received.")
                return None
        else:
            print("Invalid transformation data format.")
            return None
    else:
        print("No valid frame data received.")
        return None

def print_matrices(matrices):
    """Prints transformation matrices in a readable format."""
    for i, matrix in enumerate(matrices):
        print(f"Transform {i+1}:")
        for row in matrix:
            print("  ".join(f"{value:10.4f}" for value in row))
        print()

def key_listener_thread():
    """Thread that listens for key presses to capture data."""
    global stop_threads, capture_requested
    
    while not stop_threads:
        if select.select([sys.stdin], [], [], 0.01)[0]:  # Non-blocking key check
            key = sys.stdin.read(1).strip().lower()
            
            if key == 's':
                capture_requested = True
                print("\nCapture requested...")
                
            elif key == 'q':
                stop_threads = True
                print("\nStopping all threads...")

def tracker_thread(tracker):
    """Thread for continuously monitoring the NDI tracker."""
    global stop_threads, capture_requested, last_captures
    
    while not stop_threads:
        time.sleep(0.0001)  # 0.01 for Prevent CPU overuse
        
        if capture_requested:
            timestamp = time_since_epoch_millisec()
            transforms = get_transformations(tracker)
            
            if transforms is not None:
                # Store timestamp and transforms in the global variable
                # The video thread will add the frame and save everything
                last_captures.append((timestamp, transforms, None))
                print(f"\nTransformations captured at timestamp: {timestamp}")
                print_matrices(transforms)
            else:
                print("\nFailed to capture transformations.")
            
            capture_requested = False

def save_data(output_dir, timestamp, transforms, frame):
    """Save captured data with timestamp."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save image with timestamp in filename
    if frame is not None:
        image_filename = os.path.join(output_dir, f"frame_{timestamp}.png")
        cv2.imwrite(image_filename, frame)
        print(f"Frame saved to {image_filename}")
    
    # Save transforms to CSV
    if transforms is not None and len(transforms) > 0:
        csv_filename = os.path.join(output_dir, f"transforms_{timestamp}.csv")
        with open(csv_filename, "w", newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header row with timestamp
            csv_writer.writerow(["timestamp", timestamp])
            
            # Write each transform
            for i, matrix in enumerate(transforms):
                row = [f"transform_{i+1}"] + matrix.flatten().tolist()
                csv_writer.writerow(row)
        
        print(f"Transforms saved to {csv_filename}")

def main():
    global stop_threads, last_captures
    
    # Create output directory with timestamp
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"capture_{current_time}"
    
    # Set up NDI tracker
    settings_vega = {
        "tracker type": "polaris",
        # Update ROM file path to your actual path
        "romfiles": ["D:\\Softwares\\Northern Digital Inc\\Installer and some ROMs\\tracker (1)\\8700340- Polaris Passive 4-Marker Probe.rom"]
    }
    
    print("Initializing NDI tracker...")
    tracker = NDITracker(settings_vega)
    tracker.start_tracking()
    print("Tracker initialized. Waiting 5 seconds before proceeding...")
    time.sleep(5)  # Allow Polaris to detect tools properly
    
    # Set up video capture
    print("Opening video capture...")
    cap = cv2.VideoCapture(0)  # Change index if needed
    
    if not cap.isOpened():
        print("Error: Could not open video source")
        tracker.stop_tracking()
        tracker.close()
        return

    # Get best available resolution
    available_resolutions, best_resolution = get_available_resolutions(cap)
    print(f"Available resolutions: {available_resolutions}")
    print(f"Using resolution: {best_resolution}")

    frame_width, frame_height = best_resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    # Start key listener thread
    print("Starting key listener thread...")
    key_thread = threading.Thread(target=key_listener_thread, daemon=True)
    key_thread.start()
    
    # Start tracker thread
    print("Starting tracker thread...")
    tracker_thread_instance = threading.Thread(target=tracker_thread, args=(tracker,), daemon=True)
    tracker_thread_instance.start()
    
    print("\nSystem ready!")
    print("Press 's' to capture a frame with transforms")
    print("Press 'q' to quit")
    
    # FPS tracking
    old_time = 0
    fps_counter = 0
    
    try:
        while not stop_threads:
            # Capture frame from video source
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Calculate FPS
            new_time = time_since_epoch_millisec()
            if old_time != 0:
                fps_counter = 1000.0 / (new_time - old_time)
            old_time = new_time
            
            # Display FPS on frame
            cv2.putText(frame, f"FPS: {fps_counter:.2f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Check if there are any captures waiting for frames
            for i, (timestamp, transforms, _) in enumerate(last_captures):
                if last_captures[i][2] is None:  # No frame assigned yet
                    # Add current frame to the capture
                    last_captures[i] = (timestamp, transforms, frame.copy())
                    
                    # Save data
                    save_data(output_dir, timestamp, transforms, frame.copy())
            
            # Remove processed captures
            last_captures = [capture for capture in last_captures if capture[2] is None]
            
            # Show frame
            cv2.imshow("Video Feed", frame)
            
            # Check for key presses in the OpenCV window
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                capture_requested = True
                print("\nCapture requested from OpenCV window...")
            elif key == ord('q'):
                stop_threads = True
            
    except KeyboardInterrupt:
        print("\nCapture stopped by user.")
    
    finally:
        # Clean up
        print("Cleaning up...")
        stop_threads = True
        cap.release()
        cv2.destroyAllWindows()
        tracker.stop_tracking()
        tracker.close()
        print("Done!")

if __name__ == "__main__":
    main()