import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QDoubleSpinBox
import zmq


class HoloLensCoordinatorApp(QWidget):
    def __init__(self):
        super().__init__()
        
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

    def startRecording(self):
        self.publisher.send_string("DataCollection: Start Recording")
        self.startButton.setText("Recording Sent!")

    def stopRecording(self):
        self.publisher.send_string("DataCollection: Stop Recording")
        self.startButton.setText("Start Recording!")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HoloLensCoordinatorApp()
    window.show()
    sys.exit(app.exec_())
