import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QDoubleSpinBox
from PyQt5.QtCore import QThread, pyqtSignal
import zmq
from datetime import datetime
import cv2
import numpy as np
import time
from datetime import datetime
import csv
import os
import argparse

sys.path.append("../")
from Data_Logger import main
# Data_Logger = __import__("Data Logger")

def time_since_epoch_millisec():
    return int(round(time.time() * 1000))

class VideoRecordingThread(QThread):
    updateSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.isRunning = True  # A flag to control the loop
        self.isRecording = False
        # Check for command line arguments
        if len(sys.argv) < 3:
            print("Usage: python script.py <fps> <output_filename>")
            return

        self.fps = int(sys.argv[1])
        self.raw_output_filename = sys.argv[2]

        curT = datetime.now()
        tString = curT.strftime("%Y%m%d_%H%M%S")
        self.output_filename = self.raw_output_filename + ("_" + tString)

    def run(self):
        self.isRunning == True
        # Create a VideoCapture object and use camera to capture the video
        cap = cv2.VideoCapture(3)  # Change the index based on your camera
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
        assert(frame_height == frame_height_act)

        print(f"Recording Frames to {self.output_filename}, with shape ({frame_width}, {frame_height})")
        
        frame_no = 0
        old_time = 0
        fps_counter = 0

        # Open a CSV file to store timestamps
        with open(f"{self.output_filename}.csv", "w", newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Define the codec and create VideoWriter object
            video_writer = cv2.VideoWriter(f"{self.output_filename}.avi", 
                                            cv2.VideoWriter_fourcc(*'MJPG'), 
                                            self.fps, 
                                            (frame_width, frame_height))
            while self.isRunning:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate FPS
                new_time = time_since_epoch_millisec()
                if old_time != 0:
                    fps_counter = 1000.0 / (new_time - old_time)
                old_time = new_time

                if self.isRecording:
                    # Write the frame into the file
                    video_writer.write(frame)
                    # Log the frame number and timestamp
                    csv_writer.writerow([frame_no, time_since_epoch_millisec()])
                    print(f"\rRecording FPS: {fps_counter:.2f}. Shape: {frame.shape}", end="\r")
                    frame_no += 1
                else:
                    # pass
                    print(f"\rFPS: {fps_counter:.2f}. Shape: {frame.shape}", end="\r")

                # Display the resulting frame
                cv2.imshow("Frame", frame)

                # Press ESC to exit, SPACE to start recording
                key = cv2.waitKey(1)
                if key == 27:  # ESC key
                    break
                if key == 32:  # SPACE key
                    self.isRecording = True
                    print("Recording started")
        print("")
        # Release everything when done
        cap.release()
        video_writer.release()
        cv2.destroyAllWindows()
    
    def stop(self):
        self.isRunning = False
        curT = datetime.now()
        tString = curT.strftime("%Y%m%d_%H%M%S")
        self.output_filename = self.raw_output_filename + ("_" + tString)
        
    
    def startRecording(self):
        self.isRecording = True

    def stopRecording(self):
        self.isRecording = False

class HoloLensCoordinatorApp(QWidget):
    def __init__(self):
        super().__init__()

        self.start_time = 0
        
        # ZeroMQ Publisher Setup
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:7788")  # Adjust the port if needed

        # GUI Elements
        self.setWindowTitle("HoloLens Coordinator")
        mainLayout = QVBoxLayout()
        gridLayout = QGridLayout()

        # Recording Buttons
        self.startButton = QPushButton("Start Recording")
        self.stopButton = QPushButton("Stop Recording")
        self.startButton.clicked.connect(self.startRecording)
        self.stopButton.clicked.connect(self.stopRecording)
        mainLayout.addWidget(self.startButton)
        mainLayout.addWidget(self.stopButton)

        # Cursor Visual Dropdowns
        dropdownLabels = [
            "User 0 - Self Cursor Style:",
            "User 1 - Self Cursor Style:",
            "User 0 - Other Cursor Style:",
            "User 1 - Other Cursor Style:"
        ]
        self.dropdowns = []

        for i, label in enumerate(dropdownLabels):
            lbl = QLabel(label)
            dropdown = QComboBox()
            # dropdown.addItems(["Hide", "Style1", "Style2", "Style3", "Style4"])
            dropdown.addItems(["Hide", "Style1", "Style2", "Style3"])
            dropdown.currentIndexChanged.connect(
                lambda idx, i=i: self.changeCursorVisual(i, idx)
            )
            self.dropdowns.append(dropdown)

            gridLayout.addWidget(lbl, i // 2, (i % 2) * 2)  # 2 columns
            gridLayout.addWidget(dropdown, i // 2, (i % 2) * 2 + 1)

        mainLayout.addLayout(gridLayout)

        # Cursor Size Input
        self.cursorSizeInput = QDoubleSpinBox()
        self.cursorSizeInput.setRange(0.0, 1.0) 
        self.cursorSizeInput.setSingleStep(0.1) 
        self.cursorSizeInput.valueChanged.connect(self.changeCursorSize)
        mainLayout.addWidget(QLabel("Cursor Size:"))
        mainLayout.addWidget(self.cursorSizeInput)

        self.dropdowns[0].setCurrentIndex(0) # Hiding Surgeon's Own Cursor
        self.dropdowns[1].setCurrentIndex(0) # Hiding Trainee's Own Cursor
        self.dropdowns[2].setCurrentIndex(0) # Hiding Surgeon's Other Cursor
        self.dropdowns[3].setCurrentIndex(2) # Showing Trainee's Other Cursor
        self.cursorSizeInput.setValue(0.25)

        self.setLayout(mainLayout)

        self.recordingThread = None
        self.startVideo()

    def startVideo(self):
        if self.recordingThread is None or not self.recordingThread.isRunning:
            self.recordingThread = VideoRecordingThread()
            self.recordingThread.updateSignal.connect(self.displayMessage)
            self.recordingThread.start()

    def startVideoRecording(self):
        if self.recordingThread is None or not self.recordingThread.isRunning:
            self.recordingThread = VideoRecordingThread()
            self.recordingThread.updateSignal.connect(self.displayMessage)
            self.recordingThread.start()
        
        self.recordingThread.startRecording()
            # self.startButton.setEnabled(False)
            # self.stopButton.setEnabled(True)

    def startRecording(self):
        self.publisher.send_string("DataCollection: Start Recording")
        self.startButton.setText("Recording Sent!")
        self.start_time = datetime.now()
        print(f"Recording Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.startVideoRecording()
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def stopVideoRecording(self):
        if self.recordingThread and self.recordingThread.isRunning:
            self.recordingThread.stop()
            self.recordingThread.wait()  # Ensure the thread finishes before exiting
            self.recordingThread = None
            # self.startButton.setEnabled(True)
            # self.stopButton.setEnabled(False)
        self.startVideo()

    def stopRecording(self):
        self.publisher.send_string("DataCollection: Stop Recording")
        self.startButton.setText("Start Recording!")
        # Record the end time
        end_time = datetime.now()
        elapsed_time = (end_time - self.start_time).total_seconds()
        print(f"Recording End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed Time: {elapsed_time} sec")
        self.stopVideoRecording()
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)



    def changeCursorVisual(self, dropdownIndex, style):
        userMap = {
            0: "User1/MyCursorVisual",
            1: "User2/MyCursorVisual",
            2: "User1/OtherCursorVisual",
            3: "User2/OtherCursorVisual"
        }
        topic = f"{userMap[dropdownIndex]}"
        if style == 3:
            style += 1
        msg = f"{topic}: {style}"
        self.publisher.send_string(msg)
        print(msg)

    def changeCursorSize(self, size):
        msg = f"CursorSize: {size}"
        self.publisher.send_string(msg)
        print(msg)
    
    def displayMessage(self, message):
        print(message)  # Optional: Display messages from the thread

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HoloLensCoordinatorApp()
    window.show()
    sys.exit(app.exec_())
