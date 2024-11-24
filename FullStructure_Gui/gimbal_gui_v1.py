import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time
import math

class MotorControllerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Drone Controller with Roll and Pitch")

        self.serial_port = None

        # Serial port selection
        self.port_label = tk.Label(master, text="Select Serial Port:")
        self.port_label.pack()

        self.port_combo = ttk.Combobox(master, values=self.list_serial_ports())
        self.port_combo.pack()

        self.connect_button = tk.Button(master, text="Connect", command=self.connect_serial)
        self.connect_button.pack()

        # Drone canvas
        self.canvas = tk.Canvas(master, width=400, height=400, bg="lightgray")
        self.canvas.pack(pady=10)
        self.drone_center = (200, 200)
        self.drone_size = 50
        self.draw_drone()

        self.canvas.bind("<B1-Motion>", self.drag_drone)

        # Motor values
        self.motor_values = [1100, 1100, 1100, 1100]  # Initial motor values

        # Arm button
        self.arm_button = tk.Button(master, text="Arm", command=self.arm_motors)
        self.arm_button.pack()

        # Stop all button
        self.stop_button = tk.Button(master, text="Stop All Motors", command=self.stop_all_motors)
        self.stop_button.pack()

        # Serial monitor
        self.serial_monitor = tk.Text(master, height=10, width=50)
        self.serial_monitor.pack()

    def list_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_serial(self):
        port = self.port_combo.get()
        try:
            self.serial_port = serial.Serial(port, 115200, timeout=1)
            self.serial_monitor.insert(tk.END, f"Connected to {port}\n")
        except Exception as e:
            self.serial_monitor.insert(tk.END, f"Error: {e}\n")

    def arm_motors(self):
        if self.serial_port:
            self.serial_port.write(b'A\n')
            self.serial_monitor.insert(tk.END, "Armed motors.\n")

    def stop_all_motors(self):
        if self.serial_port:
            self.serial_port.write(b'S\n')
            self.serial_monitor.insert(tk.END, "Stopped all motors.\n")
        self.motor_values = [1100, 1100, 1100, 1100]  # Reset motor values
        self.update_serial()

    def draw_drone(self):
        """Draw the drone representation."""
        x, y = self.drone_center
        size = self.drone_size
        self.canvas.delete("drone")
        self.canvas.create_oval(x - size, y - size, x + size, y + size, fill="blue", tags="drone")
        self.canvas.create_line(x, y - size, x, y + size, width=3, fill="red", tags="drone")  # Pitch axis
        self.canvas.create_line(x - size, y, x + size, y, width=3, fill="green", tags="drone")  # Roll axis

    def drag_drone(self, event):
        """Handle mouse drag to control roll and pitch."""
        dx = event.x - self.drone_center[0]
        dy = event.y - self.drone_center[1]

        # Calculate roll and pitch changes
        roll = max(-1, min(1, dx / 50))  # Normalize to -1 to 1
        pitch = max(-1, min(1, dy / 50))  # Normalize to -1 to 1

        # Update motor values
        self.motor_values[0] = 1100 + int(200 * roll)  # Motor 1 for roll
        self.motor_values[2] = 1100 - int(200 * roll)  # Motor 3 for roll
        self.motor_values[1] = 1100 + int(200 * pitch)  # Motor 2 for pitch
        self.motor_values[3] = 1100 - int(200 * pitch)  # Motor 4 for pitch

        # Update the drone and serial communication
        self.draw_drone()
        self.update_serial()

    def update_serial(self):
        """Send motor values to the serial port."""
        if self.serial_port:
            motor_values_str = ",".join(map(str, self.motor_values))
            self.serial_port.write(f"{motor_values_str}\n".encode())
            self.serial_monitor.insert(tk.END, f"Motor values set: {motor_values_str}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControllerApp(root)
    root.mainloop()
