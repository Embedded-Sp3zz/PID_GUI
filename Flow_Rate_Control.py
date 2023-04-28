"""
Flow_Rate_Control.py

Written by: Brian Hinger 4/25/2023

Flow Rate Control Script
This script provides a GUI for controlling the flow rate of fluid out of a pressurized reservoir.
"""

# info DIN PID Controller - Flow Control: https://www.miinet.com/pharmaceuticals-and-biotechnology/1-4-din-pid-controller-flow-control
# info tuning a PID Controller - https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=9013#:~:text=To%20tune%20your%20PID%20controller,to%20roughly%20half%20this%20value.

import serial
import os
import sys
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSlider, QPushButton, QVBoxLayout, QWidget, QSizePolicy, QSpinBox, QHBoxLayout
from PyQt5.QtCore import QTimer, QRunnable, QThreadPool, Qt
from simple_pid import PID
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Constants
MIN_FLOW_RATE = 0
MAX_FLOW_RATE = 100
UPDATE_RATE_MS = 1000
SERIAL_PORT = '/dev/ttyUSB0'  # Serial port for the pinch valve
SERIAL_BAUDRATE = 9600  # Baud rate for the pinch valve
KP = 2  # Proportional gain for PID controller
KI = 1  # Integral gain for PID controller
KD = 2  # Derivative gain for PID controller
INITIAL_POSITION = 0  # Initial valve position
VALVE_POSITIONS = 400  # Total valve positions
WEIGHT_CALIBRATION_FACTOR = 9  # Weight calibration factor (in g/s)
WEIGHT_DATA_DIR = "weight_data_files"  # Directory for weight data files


class FlowRateControl:
    """
    The main class for controlling the flow rate of fluid.
    """
    def __init__(self, kp, ki, kd, setpoint=0):
        self.create_data_dir()
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        self.weight_file_path = os.path.join(WEIGHT_DATA_DIR, f"weight_data_{now_str}.npy")
        self.pid = PID(kp, ki, kd, setpoint=setpoint)
        self.thread_pool = QThreadPool()

    def create_data_dir(self):
        """
        Create the directory for the weight data files if it doesn't exist.
        """
        os.makedirs(WEIGHT_DATA_DIR, exist_ok=True)

    def update_flow_rate_setpoint(self, flow_rate):
        """
        Update PID setpoint based on user input.
        """
        self.pid.setpoint = flow_rate

    def write_weight_data(self, flow_rate):
        """
        Increase the weight artificially based on the flow rate and write to a numpy file.
        """
        try:
            current_data = np.load(self.weight_file_path)
        except FileNotFoundError:
            current_data = np.array([])
        self.weight = current_data[-1] + flow_rate if current_data.size else flow_rate
        current_data = np.append(current_data, self.weight)
        np.save(self.weight_file_path, current_data)

    def read_weight_data(self):
        """
        Load weight data from the current weight file.
        """
        try:
            weight_data = np.load(self.weight_file_path)
        except FileNotFoundError:
            weight_data = np.array([0,0])
        return weight_data

    def calculate_flow_rate(self, weight_data):
        """
        Calculate the flow rate based on the change in weight.
        """
        return weight_data[-1] - weight_data[-2] if len(weight_data) >= 2 else 0

    def update_data(self):
        """
        Update data every second. Triggered by QTimer.
        """
        weight_data = self.read_weight_data()
        current_flow_rate = self.calculate_flow_rate(weight_data)
        valve_position = int(self.pid(current_flow_rate))
        valve_position = max(0, min(VALVE_POSITIONS, valve_position))
        worker = Worker(self.set_valve_position, valve_position)
        self.thread_pool.start(worker)
        self.write_weight_data(valve_position/WEIGHT_CALIBRATION_FACTOR)
        return current_flow_rate, valve_position

    def set_valve_position(self, position):
        """
        Set valve position via serial connection.
        """
        command = f"/1A{position}R\r\n"
        print(command)
        # Uncomment the line below when connected to the hardware.
        # self.serial_conn.write(command.encode())


class FlowRateUI(QMainWindow):
    """
    GUI interface for controlling the flow rate of fluid.
    """
    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.setWindowTitle("Flow Rate Control")
        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(UPDATE_RATE_MS)

    def initUI(self):
        """
        Initialize the user interface.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()

        control_layout = QVBoxLayout()

        self.flow_rate_label = QLabel("Desired Flow Rate (mL/s):")
        control_layout.addWidget(self.flow_rate_label)

        self.flow_rate_slider = QSlider(Qt.Vertical)
        self.flow_rate_slider.setMinimum(MIN_FLOW_RATE)
        self.flow_rate_slider.setMaximum(MAX_FLOW_RATE)
        control_layout.addWidget(self.flow_rate_slider)

        self.flow_rate_input = QSpinBox()
        self.flow_rate_input.setMinimum(MIN_FLOW_RATE)
        self.flow_rate_input.setMaximum(MAX_FLOW_RATE)
        control_layout.addWidget(self.flow_rate_input)

        self.flow_rate_slider.valueChanged.connect(self.flow_rate_input.setValue)
        self.flow_rate_input.valueChanged.connect(self.flow_rate_slider.setValue)

        self.flow_rate_slider.setValue(INITIAL_POSITION)

        self.set_flow_rate_button = QPushButton("Set Flow Rate")
        control_layout.addWidget(self.set_flow_rate_button)

        self.current_flow_rate_label = QLabel("Current Flow Rate (mL/s): 0")
        control_layout.addWidget(self.current_flow_rate_label)

        self.valve_position_label = QLabel("Valve Position:")
        control_layout.addWidget(self.valve_position_label)

        self.set_flow_rate_button.clicked.connect(self.update_flow_rate_setpoint)

        layout.addLayout(control_layout)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        central_widget.setLayout(layout)

    def update_flow_rate_setpoint(self):
        """
        Update PID setpoint based on user input.
        """
        try:
            flow_rate = float(self.flow_rate_input.text())
            self.controller.pid.setpoint = flow_rate
        except ValueError:
            print("Invalid input for flow rate. Please enter a valid number.")

    def update_data(self):
        """
        Update data every second. Triggered by QTimer.
        """
        current_flow_rate, valve_position = self.controller.update_data()

        self.current_flow_rate_label.setText(f"Current Flow Rate (mL/s): {current_flow_rate:.2f}")
        self.valve_position_label.setText(f"Valve Position: {valve_position}")

        self.plot_data()

    def plot_data(self):
        """
        Plot flow rate data and weight data.
        """
        self.figure.clear()

        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        weight_data = self.controller.read_weight_data()
        flow_rate_data = np.diff(weight_data)

        ax1.plot(flow_rate_data)
        ax1.set_title("Flow Rate Over Time")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Flow Rate (mL/s)")

        ax2.plot(weight_data)
        ax2.set_title("Weight Over Time")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Weight (g)")

        self.canvas.draw()


class Worker(QRunnable):
    """
    Worker thread for non-blocking operations.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Run the specified function with given arguments.
        """
        self.fn(*self.args, **self.kwargs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = FlowRateControl(KP, KI, KD)
    window = FlowRateUI(controller)
    window.show()
    sys.exit(app.exec_())



