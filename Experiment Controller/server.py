import sys
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
import zmq


class HoloLensCoordinatorApp(QWidget):
    """Simple ZeroMQ publisher with a minimal Qt‑based control panel."""

    def __init__(self):
        super().__init__()

        # ──────────────── ZMQ SET‑UP ────────────────
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:7788")  # Change port as needed

        # ──────────────── STATE ────────────────
        self.record_start_time: datetime | None = None
        # Generic tracking for all Start / Stop toggles
        self.ops = [
            "AppOperation",
            # "ArUcoOperation",
            # "GazeShareOperation",
            # # "GazeTrackOperation",
            # "GazeSaveOperation",
        ]
        self.operation_active = {op: True for op in self.ops}
        self.operation_buttons: dict[str, QPushButton] = {}

        # ──────────────── UI BUILD ────────────────
        self.setWindowTitle("HoloLens Coordinator")
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        # Recording controls
        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.stop_button)

        # Operation toggles – generated programmatically
        # NOTE: generic factory avoids five near‑identical click‑handlers.
        for op in self.ops:
            display = op.replace("Operation", "")
            btn = QPushButton(f"Stop {display}")
            # Lambda captures current *op* via default arg → avoids the classic late‑binding bug.
            btn.clicked.connect(lambda _=True, op=op: self.toggle_operation(op))
            self.operation_buttons[op] = btn
            main_layout.addWidget(btn)

        # Cursor style dropdowns
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

        # Cursor size widget
        self.cursor_size_input = QDoubleSpinBox()
        self.cursor_size_input.setRange(0.0, 1.0)
        self.cursor_size_input.setSingleStep(0.1)
        self.cursor_size_input.valueChanged.connect(self.change_cursor_size)
        main_layout.addWidget(QLabel("Cursor Size:"))
        main_layout.addWidget(self.cursor_size_input)

        # Default GUI state
        self.dropdowns[0].setCurrentIndex(0)
        self.dropdowns[1].setCurrentIndex(0)
        self.dropdowns[2].setCurrentIndex(0)
        self.dropdowns[3].setCurrentIndex(2)
        self.cursor_size_input.setValue(0.25)

        self.setLayout(main_layout)

    # ──────────────── RECORDING ────────────────
    def start_recording(self):
        self.publisher.send_string("DataCollection: Start Recording")
        self.start_button.setText("Recording Sent!")
        self.record_start_time = datetime.now()
        print("DataCollection: Start Recording")

    def stop_recording(self):
        self.publisher.send_string("DataCollection: Stop Recording")
        self.start_button.setText("Start Recording")
        end_time = datetime.now()
        if self.record_start_time:
            elapsed = (end_time - self.record_start_time).total_seconds()
            print(f"Elapsed Time: {elapsed:.1f} sec")
        print("DataCollection: Stop Recording")

    # ──────────────── GENERIC TOGGLE ────────────────
    def toggle_operation(self, op_name: str):
        """Publish Start / Stop for *op_name* and swap button label."""
        active = self.operation_active[op_name]
        display = op_name.replace("Operation", "")
        action = "Stop" if active else "Start"
        self.publisher.send_string(f"{op_name}: {action}")
        print(f"{op_name}: {action}")
        # Update UI
        new_label = (
            f"Start {display}" if active else f"Stop {display}"
        )
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
        if style == 3:  # Style3 maps to 4 in Unity – consider aligning enums.
            style += 1
        topic = topic_map[dropdown_index]
        msg = f"{topic}: {style}"
        self.publisher.send_string(msg)
        print(msg)

    def change_cursor_size(self, size: float):
        msg = f"CursorSize: {size}"
        self.publisher.send_string(msg)
        print(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HoloLensCoordinatorApp()
    window.show()
    sys.exit(app.exec_())

# NOTE: For greater scalability consider moving repeated string literals to constants
# or an enum‑like structure and reading UI layout from a configuration file.
