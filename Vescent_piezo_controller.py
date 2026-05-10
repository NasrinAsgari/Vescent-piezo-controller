import sys
import serial
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QDial, QLineEdit
)
from PyQt5.QtCore import Qt


class HVControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vescent HV Control")
        self.setGeometry(100, 100, 300, 300)

        # Serial connection
        PORT = "COM6"
        BAUDRATE = 9600
        self.ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(0.5)  # Let serial stabilize

        self.channel = 1
        self.hv_status = False  # Output initially off

        # --- UI Elements ---
        self.voltage_label = QLabel("Voltage: 0.00 V", self)
        self.voltage_label.setAlignment(Qt.AlignCenter)

        self.feedback_label = QLabel("Response: ", self)
        self.feedback_label.setAlignment(Qt.AlignCenter)

        self.dial = QDial(self)
        self.dial.setFixedSize(200, 200)
        self.dial.setRange(0, 20000)  # Maps to 0–200 V with 0.01 V steps
        self.dial.setValue(0)
        self.dial.setNotchesVisible(True)
        self.dial.valueChanged.connect(self.set_voltage)

        self.voltage_input = QLineEdit(self)
        self.voltage_input.setPlaceholderText("Enter Voltage (V)")
        self.voltage_input.returnPressed.connect(self.apply_entered_voltage)

        self.btn_on = QPushButton("HV ON", self)
        self.btn_on.clicked.connect(self.hv_on)

        self.btn_off = QPushButton("HV OFF", self)
        self.btn_off.clicked.connect(self.hv_off)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.voltage_label)
        layout.addWidget(self.dial)
        layout.addWidget(self.voltage_input)
        layout.addWidget(self.btn_on)
        layout.addWidget(self.btn_off)
        layout.addWidget(self.feedback_label)
        self.setLayout(layout)

        self.set_knob_color()  # Initialize knob color

    def set_voltage(self, value):
        voltage = value / 100.0  # Convert to volts
        command = f"DCBiasv {self.channel} {voltage:.2f}\r"
        self.ser.write(command.encode())
        time.sleep(0.1)
        response = self.ser.read_all().decode().strip()

        self.voltage_label.setText(f"Voltage: {voltage:.2f} V")
        try:
            formatted_response = f"{float(response):.2f}" if response else "No response"
        except ValueError:
            formatted_response = response if response else "No response"
        self.feedback_label.setText(f"Response: {formatted_response}")

    def apply_entered_voltage(self):
        try:
            voltage = float(self.voltage_input.text())
            if 0 <= voltage <= 200:
                command = f"DCBiasv {self.channel} {voltage:.2f}\r"
                self.ser.write(command.encode())
                time.sleep(0.1)
                response = self.ser.read_all().decode().strip()

                self.voltage_label.setText(f"Voltage: {voltage:.2f} V")
                self.dial.setValue(int(voltage * 100))  # Sync dial
                try:
                    formatted_response = f"{float(response):.2f}" if response else "No response"
                except ValueError:
                    formatted_response = response if response else "No response"
                self.feedback_label.setText(f"Response: {formatted_response}")
            else:
                self.feedback_label.setText("Voltage must be 0–200 V")
        except ValueError:
            self.feedback_label.setText("Invalid voltage")

    def hv_on(self):
        command = f"CONTROL {self.channel} 3\r"  # Enable output (20 V/V)
        self.ser.reset_input_buffer()
        self.ser.write(command.encode())
        time.sleep(0.1)
        response = self.ser.read_all().decode().strip()
        formatted_response = f"{float(response):.2f}" if response else "HV ON command sent"
        self.feedback_label.setText(f"Response: {formatted_response}")
        self.hv_status = True
        self.set_knob_color()

    def hv_off(self):
        command = f"CONTROL {self.channel} 0\r"  # Disable output
        self.ser.reset_input_buffer()
        self.ser.write(command.encode())
        time.sleep(0.1)
        response = self.ser.read_all().decode().strip()
        self.feedback_label.setText(f"Response: {response if response else 'HV OFF command sent'}")
        self.hv_status = False
        self.set_knob_color()

    def set_knob_color(self):
        if self.hv_status:
            self.dial.setStyleSheet("""
                QDial {
                    background-color: lightgreen;
                    border-radius: 100px;
                    border: 3px solid #4CAF50;
                }
            """)
        else:
            self.dial.setStyleSheet("""
                QDial {
                    background-color: lightgray;
                    border-radius: 100px;
                    border: 3px solid #888;
                }
            """)

    def closeEvent(self, event):
        try:
            self.hv_off()
            self.ser.close()
        except:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HVControlGUI()
    window.show()
    sys.exit(app.exec_())
