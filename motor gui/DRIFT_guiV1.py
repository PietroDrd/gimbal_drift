import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MotorControllerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Motor Controller")

        self.serial_port = None

        # Serial port selection
        self.port_label = tk.Label(master, text="Select Serial Port:")
        self.port_label.pack()

        self.port_combo = ttk.Combobox(master, values=self.list_serial_ports())
        self.port_combo.pack()

        self.connect_button = tk.Button(master, text="Connect", command=self.connect_serial)
        self.connect_button.pack()

        # Slider controls for motors with range 1000 to 1500
        self.sliders = []
        for i in range(4):
            slider = tk.Scale(master, from_=1000, to=1500, orient='horizontal', label=f'Motor {i+1}', command=self.update_motors)
            slider.pack()
            self.sliders.append(slider)

        self.master_slider = tk.Scale(master, from_=1000, to=1500, orient='horizontal', label='Master Control', command=self.update_master)
        self.master_slider.pack()

        # Arm button
        self.arm_button = tk.Button(master, text="Arm", command=self.arm_motors)
        self.arm_button.pack()

        # Stop all button
        self.stop_button = tk.Button(master, text="Stop All Motors", command=self.stop_all_motors)
        self.stop_button.pack()

        # "RUN" button to set all motors to 1100 (idle)
        self.run_button = tk.Button(master, text="RUN", command=self.run_motors)
        self.run_button.pack()

        # Serial monitor
        self.serial_monitor = tk.Text(master, height=10, width=50)
        self.serial_monitor.pack()

        # Initialize plot window
        self.plot_window = tk.Toplevel(self.master)
        self.plot_window.title("Motor Inputs Plots")

        self.fig, self.axes = plt.subplots(2, 2, figsize=(8, 6))
        self.fig.suptitle("Motor Inputs Over Time")
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_window)
        self.canvas.get_tk_widget().pack()

        self.plot_data = [[], [], [], []]  # Store motor values
        self.time_data = []  # Time points

    def list_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_serial(self):
        port = self.port_combo.get()
        try:
            self.serial_port = serial.Serial(port, 115200, timeout=1)
            self.serial_monitor.insert(tk.END, f"Connected to {port}\n")
            self.master.after(1000, self.read_serial)
        except Exception as e:
            self.serial_monitor.insert(tk.END, f"Error: {e}\n")

    def read_serial(self):
        if self.serial_port and self.serial_port.in_waiting:
            data = self.serial_port.read(self.serial_port.in_waiting)
            self.serial_monitor.insert(tk.END, f"Received: {data.decode()}\n")
        self.master.after(100, self.read_serial)

    def arm_motors(self):
        if self.serial_port:
            self.serial_port.write(b'A\n')  # Send arm command
            self.serial_monitor.insert(tk.END, "Armed motors.\n")

    def stop_all_motors(self):
        if self.serial_port:
            self.serial_port.write(b'S\n')  # Send stop command
            self.serial_monitor.insert(tk.END, "Stopped all motors.\n")
        
        # Set all sliders to their minimum value (1000)
        for slider in self.sliders:
            slider.set(1000)
        self.update_motors()  # Update motor values to minimum

    def update_master(self, event=None):
        # Set all motor sliders to the value of the master slider
        for slider in self.sliders:
            slider.set(self.master_slider.get())  # Update each slider with the master value
        self.update_motors()  # Update motor values after master change

    def update_motors(self, event=None):
        if self.serial_port:
            # Create a string with motor values from each slider
            motor_values = ",".join(str(slider.get()) for slider in self.sliders)
            self.serial_port.write(f"{motor_values}\n".encode())  # Send motor values as a string
            self.serial_monitor.insert(tk.END, f"Motor values set: {motor_values}\n")

        # Update motor values in the plot
        self.update_plots()

    def update_plots(self):
        current_time = time.time()

        # Add new data point to time and motor data lists
        if not self.time_data:
            self.time_data.append(0)  # Start at t=0
        else:
            self.time_data.append(self.time_data[-1] + 1)  # Increment time

        for i in range(4):
            self.plot_data[i].append(self.sliders[i].get())

        # Update plots for each motor
        for i, ax in enumerate(self.axes.flatten()):
            ax.clear()  # Clear old plot
            ax.plot(self.time_data, self.plot_data[i])  # Plot new data
            ax.set_title(f'Motor {i+1}')
            ax.set_ylim([1000, 1500])  # Set limits for y-axis (motor value range)

        self.fig.tight_layout()
        self.canvas.draw()

    def run_motors(self):
        # Set all motor sliders to 1100 (idle value)
        for slider in self.sliders:
            slider.set(1100)
        self.update_motors()  # Send updated values to motors
        self.serial_monitor.insert(tk.END, "Set all motors to idle value (1100).\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControllerApp(root)
    root.mainloop()
