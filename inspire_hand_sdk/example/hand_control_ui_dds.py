"""
DDS Hand Control UI (Inspire)

Controls Inspire hands over DDS topics and plots live motor current:
  - Publish: rt/inspire_hand/ctrl/l, rt/inspire_hand/ctrl/r
  - Subscribe: rt/inspire_hand/state/l, rt/inspire_hand/state/r

Usage:
  source /home/esports/Documents/teleop_setup/inspire_hand_ws/hands-env/bin/activate
  python inspire_hand_sdk/example/hand_control_ui_dds.py --network enp39s0
"""

from __future__ import annotations

import argparse
from collections import deque
import os
import threading
from typing import Optional

# Reduce Qt/GL driver-related native crashes on some systems.
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from inspire_sdkpy import inspire_dds, inspire_hand_defaut


JOINT_NAMES = ["Pinky", "Ring", "Middle", "Index", "Thumb Bend", "Thumb Rot"]


class HandDDSIO:
    def __init__(self, side: str):
        assert side in ("l", "r")
        self.side = side
        self._state_lock = threading.Lock()
        self._state: Optional[inspire_dds.inspire_hand_state] = None

        self._pub = ChannelPublisher(f"rt/inspire_hand/ctrl/{self.side}", inspire_dds.inspire_hand_ctrl)
        self._pub.Init()

        self._sub = ChannelSubscriber(
            f"rt/inspire_hand/state/{self.side}",
            inspire_dds.inspire_hand_state,
        )
        self._sub.Init(self._on_state, 10)

    def _on_state(self, msg: inspire_dds.inspire_hand_state):
        with self._state_lock:
            self._state = msg

    def read_state(self) -> Optional[inspire_dds.inspire_hand_state]:
        with self._state_lock:
            return self._state

    def send_grasp(self, value: int, mode: str = "position"):
        value = int(np.clip(value, 0, 1000))
        cmd = inspire_hand_defaut.get_inspire_hand_ctrl()
        cmd.pos_set = [value] * 6
        cmd.angle_set = [value] * 6
        cmd.force_set = [300] * 6
        cmd.speed_set = [500] * 6
        # 0b0001 angle, 0b0010 position
        cmd.mode = 0b0010 if mode == "position" else 0b0001
        self._pub.Write(cmd)


class CurrentPlotCanvas(QWidget):
    def __init__(self, history_len: int, dt_s: float):
        super().__init__()
        self.history_len = history_len
        self.dt_s = dt_s
        self.x = np.linspace(-history_len * dt_s, 0.0, history_len)

        layout = QVBoxLayout(self)
        self.plot_l = pg.PlotWidget(title="Left Hand Current")
        self.plot_r = pg.PlotWidget(title="Right Hand Current")
        layout.addWidget(self.plot_l)
        layout.addWidget(self.plot_r)

        self.plot_l.showGrid(x=True, y=True, alpha=0.3)
        self.plot_r.showGrid(x=True, y=True, alpha=0.3)
        self.plot_l.setLabel("left", "Current")
        self.plot_r.setLabel("left", "Current")
        self.plot_r.setLabel("bottom", "Time", "s")

        colors = ["#d32f2f", "#f57c00", "#fbc02d", "#388e3c", "#1976d2", "#7b1fa2"]
        self.lines_l = []
        self.lines_r = []
        for i, name in enumerate(JOINT_NAMES):
            pen = pg.mkPen(colors[i % len(colors)], width=2)
            self.lines_l.append(self.plot_l.plot(self.x, np.zeros(history_len), pen=pen, name=name))
            self.lines_r.append(self.plot_r.plot(self.x, np.zeros(history_len), pen=pen, name=name))

        self.plot_l.addLegend()
        self.plot_r.addLegend()

    def update_plot(self, left_hist: list[deque], right_hist: list[deque]):
        for i in range(6):
            self.lines_l[i].setData(self.x, np.array(left_hist[i], dtype=float))
            self.lines_r[i].setData(self.x, np.array(right_hist[i], dtype=float))


class MainWindow(QMainWindow):
    def __init__(self, dt_ms: int = 50, no_plot: bool = False):
        super().__init__()
        self.setWindowTitle("Inspire DDS Hand Control + Current Monitor")
        self.resize(1200, 800)

        self.dt_ms = dt_ms
        self.no_plot = no_plot
        self.dt_s = dt_ms / 1000.0
        self.history_len = 300
        self.tick_count = 0

        self.hand_l = HandDDSIO("l")
        self.hand_r = HandDDSIO("r")

        self.current_left_hist = [deque([0.0] * self.history_len, maxlen=self.history_len) for _ in range(6)]
        self.current_right_hist = [deque([0.0] * self.history_len, maxlen=self.history_len) for _ in range(6)]

        self.left_labels: list[QLabel] = []
        self.right_labels: list[QLabel] = []

        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.dt_ms)

    def _build_ui(self):
        root = QWidget()
        main = QVBoxLayout(root)

        control_box = QGroupBox("Control")
        control_layout = QGridLayout(control_box)

        control_layout.addWidget(QLabel("Target Hand"), 0, 0)
        self.target_hand_combo = QComboBox()
        self.target_hand_combo.addItems(["both", "left", "right"])
        control_layout.addWidget(self.target_hand_combo, 0, 1)

        control_layout.addWidget(QLabel("Mode"), 0, 2)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["position", "angle"])
        control_layout.addWidget(self.mode_combo, 0, 3)

        control_layout.addWidget(QLabel("Grasp Slider"), 1, 0)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(0)
        control_layout.addWidget(self.slider, 1, 1, 1, 3)

        self.slider_label = QLabel("0")
        control_layout.addWidget(self.slider_label, 1, 4)
        self.slider.valueChanged.connect(lambda v: self.slider_label.setText(str(v)))

        self.btn_open = QPushButton("Open (0)")
        self.btn_half = QPushButton("Half (500)")
        self.btn_close = QPushButton("Close (1000)")
        self.btn_open.clicked.connect(lambda: self.slider.setValue(0))
        self.btn_half.clicked.connect(lambda: self.slider.setValue(500))
        self.btn_close.clicked.connect(lambda: self.slider.setValue(1000))
        control_layout.addWidget(self.btn_open, 2, 1)
        control_layout.addWidget(self.btn_half, 2, 2)
        control_layout.addWidget(self.btn_close, 2, 3)

        self.btn_stop = QPushButton("Emergency Open")
        self.btn_stop.clicked.connect(self._emergency_open)
        control_layout.addWidget(self.btn_stop, 2, 4)

        main.addWidget(control_box)

        status_box = QGroupBox("Current (Latest)")
        status_layout = QGridLayout(status_box)
        status_layout.addWidget(QLabel("Joint"), 0, 0)
        status_layout.addWidget(QLabel("Left"), 0, 1)
        status_layout.addWidget(QLabel("Right"), 0, 2)
        for i, name in enumerate(JOINT_NAMES):
            status_layout.addWidget(QLabel(name), i + 1, 0)
            ll = QLabel("-")
            rr = QLabel("-")
            self.left_labels.append(ll)
            self.right_labels.append(rr)
            status_layout.addWidget(ll, i + 1, 1)
            status_layout.addWidget(rr, i + 1, 2)
        main.addWidget(status_box)

        if self.no_plot:
            main.addWidget(QLabel("Live plot disabled by --no-plot"))
            self.plot = None
        else:
            self.plot = CurrentPlotCanvas(history_len=self.history_len, dt_s=self.dt_s)
            main.addWidget(self.plot)

        self.setCentralWidget(root)

    def _selected_hands(self) -> list[HandDDSIO]:
        sel = self.target_hand_combo.currentText()
        if sel == "left":
            return [self.hand_l]
        if sel == "right":
            return [self.hand_r]
        return [self.hand_l, self.hand_r]

    def _emergency_open(self):
        self.slider.setValue(0)
        mode = self.mode_combo.currentText()
        self.hand_l.send_grasp(0, mode=mode)
        self.hand_r.send_grasp(0, mode=mode)

    def _tick(self):
        target = self.slider.value()
        mode = self.mode_combo.currentText()
        for hand in self._selected_hands():
            hand.send_grasp(target, mode=mode)

        state_l = self.hand_l.read_state()
        state_r = self.hand_r.read_state()
        curr_l = [0.0] * 6 if state_l is None else list(state_l.current)
        curr_r = [0.0] * 6 if state_r is None else list(state_r.current)

        for i in range(6):
            self.current_left_hist[i].append(float(curr_l[i]))
            self.current_right_hist[i].append(float(curr_r[i]))
            self.left_labels[i].setText(str(curr_l[i]))
            self.right_labels[i].setText(str(curr_r[i]))

        self.tick_count += 1
        if self.plot is not None and self.tick_count % 2 == 0:
            self.plot.update_plot(self.current_left_hist, self.current_right_hist)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--network", default=None, help="DDS interface, e.g. enp39s0")
    p.add_argument("--dt-ms", type=int, default=50, help="UI/control update interval in ms")
    p.add_argument("--no-plot", action="store_true", help="Disable live plotting (control + status only)")
    return p.parse_args()


def main():
    args = parse_args()
    # Workaround: some CycloneDDS builds crash with explicit interface config.
    # Use autodetect init path to avoid native buffer overflow in init.
    if args.network:
        print(
            f"[warn] --network {args.network} requested, but explicit interface init is disabled "
            "due to CycloneDDS crash. Using autodetect DDS interface."
        )
    ChannelFactoryInitialize(0)

    app = QApplication([])
    window = MainWindow(dt_ms=args.dt_ms, no_plot=args.no_plot)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
