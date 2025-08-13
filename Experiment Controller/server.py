import sys
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QDoubleSpinBox,
)
from PyQt5.QtCore import (QTimer, QThread, QObject, pyqtSignal)
import zmq

class HoloLensCoordinatorApp(QWidget):
    """Simple ZeroMQ publisher with a minimal Qt‑based control panel."""

    def __init__(self):
        super().__init__()

        # ──────────────── ZMQ SET‑UP ────────────────
        self.context = zmq.Context()
        self.port = 7788
        self.routerPort = 7789
        self.publisher = None
        self._bind_socket()

        # ──────────────── STATE ────────────────
        self.record_start_time: datetime | None = None
        self.ops = [
            "AppOperation",
            # "ArUcoOperation",
            # "GazeShareOperation",
            # "GazeTrackOperation",
            # "GazeSaveOperation",
        ]
        self.operation_active = {op: True for op in self.ops}
        self.operation_buttons: dict[str, QPushButton] = {}
        
        self.eye_gaze_positions : dict[str, str] = {}

        # ──────────────── UI BUILD ────────────────
        self.setWindowTitle("HoloLens Coordinator")
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.stop_button)

        for op in self.ops:
            display = op.replace("Operation", "")
            btn = QPushButton(f"Stop {display}")
            btn.clicked.connect(lambda _=True, op=op: self.toggle_operation(op))
            self.operation_buttons[op] = btn
            main_layout.addWidget(btn)

        dropdown_labels = [
            "User 0 – Self Cursor Style:",
            "User 1 – Self Cursor Style:",
            "User 0 – Other Cursor Style:",
            "User 1 – Other Cursor Style:",
        ]
        self.dropdowns: list[QComboBox] = []

        for i, label in enumerate(dropdown_labels):
            lbl = QLabel(label)
            dd = QComboBox()
            dd.addItems(["Hide", "Style1", "Style2", "Style3"])
            dd.currentIndexChanged.connect(lambda idx, i=i: self.change_cursor_visual(i, idx))
            self.dropdowns.append(dd)
            grid_layout.addWidget(lbl, i // 2, (i % 2) * 2)
            grid_layout.addWidget(dd, i // 2, (i % 2) * 2 + 1)

        main_layout.addLayout(grid_layout)

        self.cursor_size_input = QDoubleSpinBox()
        self.cursor_size_input.setRange(0.0, 1.0)
        self.cursor_size_input.setSingleStep(0.1)
        self.cursor_size_input.valueChanged.connect(self.change_cursor_size)
        main_layout.addWidget(QLabel("Cursor Size:"))
        main_layout.addWidget(self.cursor_size_input)

        self.dropdowns[0].setCurrentIndex(0)
        self.dropdowns[1].setCurrentIndex(0)
        self.dropdowns[2].setCurrentIndex(0)
        self.dropdowns[3].setCurrentIndex(2)
        self.cursor_size_input.setValue(0.25)

        self.setLayout(main_layout)

        # ──────────────── TIMER ──────────────── 
        self.send_timer = QTimer(self)
        self.send_timer.timeout.connect(self.send_published_eye_gaze)
        self.start_gaze_timer()

        # ──────────────── THREAD ──────────────── 
        self.thread_worker = QThread()
        self.worker = ZMQListenerThread(self)
        self.worker.moveToThread(self.thread_worker)

        self.thread_worker.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread_worker.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread_worker.finished.connect(self.thread_worker.deleteLater)

        self.thread_worker.start()

    # ──────────────── SOCKET & RETRY ────────────────
    def _bind_socket(self):
        try:
            # Bind to publisher
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://*:{self.port}")
            print(f"[ZMQ] Bound to tcp://*:{self.port}")

        except zmq.ZMQError as e:
            print(f"[ZMQ] Bind failed: {e}, retrying in 3s...")
            time.sleep(3)
            self._bind_socket()

    def send_with_retry(self, message: str, retries=5, delay=1):
        for attempt in range(retries):
            try:
                self.publisher.send_string(message)
                print(f"[ZMQ] Sent: {message}")
                return True
            except zmq.ZMQError as e:
                print(f"[ZMQ] Send of {message} failed (attempt {attempt + 1}): {e}")
                time.sleep(delay)
                # Try rebinding the socket on persistent failure
                if attempt == retries - 1:
                    self.publisher.close()
                    self._bind_socket()
        return False
    
    # ──────────────── EYE GAZE ────────────────
    def start_gaze_timer(self):
        self.send_timer.start(100)

    def send_published_eye_gaze(self):
        # Send without retry
        try:
            eye_string = f"Gaze: "
            for element in self.eye_gaze_positions.keys():
                eye_string += element + "/" + self.eye_gaze_positions[element] + ";"
            
            self.publisher.send_string(eye_string)
        except zmq.ZMQError:
            print("Was not able to send eye gaze data")

        # Restart timer until the window ends
        self.start_gaze_timer()

    # ──────────────── RECORDING ────────────────
    def start_recording(self):
        self.send_with_retry("DataCollection: Start Recording")
        self.start_button.setText("Recording Sent!")
        self.record_start_time = datetime.now()

    def stop_recording(self):
        self.send_with_retry("DataCollection: Stop Recording")
        self.start_button.setText("Start Recording")
        if self.record_start_time:
            elapsed = (datetime.now() - self.record_start_time).total_seconds()
            print(f"Elapsed Time: {elapsed:.1f} sec")

    # ──────────────── GENERIC TOGGLE ────────────────
    def toggle_operation(self, op_name: str):
        active = self.operation_active[op_name]
        display = op_name.replace("Operation", "")
        action = "Stop" if active else "Start"
        msg = f"{op_name}: {action}"
        self.send_with_retry(msg)

        new_label = f"Start {display}" if active else f"Stop {display}"
        self.operation_buttons[op_name].setText(new_label)
        self.operation_active[op_name] = not active

    # ──────────────── CURSOR CALLBACKS ────────────────
    def change_cursor_visual(self, dropdown_index: int, style: int):
        topic_map = {
            0: "User1/MyCursorVisual",
            1: "User2/MyCursorVisual",
            2: "User1/OtherCursorVisual",
            3: "User2/OtherCursorVisual",
        }
        if style == 3:
            style += 1  # Unity enum adjustment
        topic = topic_map[dropdown_index]
        msg = f"{topic}: {style}"
        self.send_with_retry(msg)

    def change_cursor_size(self, size: float):
        msg = f"CursorSize: {size}"
        self.send_with_retry(msg)

    def closeEvent(self, event):
        self.worker.stop()  # Signal worker to stop
        self.thread_worker.quit()  # Quit the thread event loop
        self.thread_worker.wait()  # Wait for thread to finish
        super().closeEvent(event)

class ZMQListenerThread(QObject):
    
    finished = pyqtSignal()
    running = True

    lastKnownBuildNumber = -1

    def __init__(self, window : HoloLensCoordinatorApp):
        super().__init__()

        self.routerPort = window.routerPort

        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind(f"tcp://*:{self.routerPort}")
        print(f"[ZMQ] Bound to tcp://*:{self.routerPort}")

        self.poller = zmq.Poller()
        self.poller.register(self.router, zmq.POLLIN)

        self.window = window

    def run(self):

        while self.running:
            socks = dict(self.poller.poll(timeout=100))  # 100ms timeout
            if self.router in socks:
                msg = self.router.recv_multipart()
                identity, content = msg
                identity = identity.decode("utf-8")
                content = content.decode("utf-8")

                # Handshake with build info (verify we don't have conflicting builds between hololens)
                if content.startswith("BUILD: "):
                    buildNumber = int(content[len("BUILD: "):])

                    print(f"A new user tried to connected with build number {buildNumber}")

                    # Update "base" build number
                    if self.lastKnownBuildNumber == -1:
                        self.lastKnownBuildNumber = buildNumber
                    # Check that the build numbers are the same
                    elif self.lastKnownBuildNumber != buildNumber:
                        print(f"First build number {self.lastKnownBuildNumber} did not match the client {identity} build number {buildNumber}")
                
                # Proceed as normal and store the eye gaze position with the identity
                else:
                    window.eye_gaze_positions[identity] = content


        print(f"[ZMQ] Listener thread stopping")
        self.router.close()
        self.context.term()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = HoloLensCoordinatorApp()
    window.show()

    sys.exit(app.exec_())