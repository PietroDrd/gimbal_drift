import serial
import signal
import sys
import time
import math


ARM_DELAY = 1
DEFAULT_DELAY = 0.2

# NOTE: Commands
# Use uppercase letters for commands that affect the python control script
# Use lowercase letters for commands that get sent to the arduino
# Dx: pause the control loop for x seconds
# Tx: set the delay between commands to x seconds; if x=0, reset back to DEFAULT_DELAY
# a: arm command; it will also pause the loop for ARM_DELAY seconds
# s: stop command; disarms the motor
# c: calib command; performs ESC calibration; performed automatically during initialization, this should not be used
# txxxx: throttle command, sets the throttle to xxxx
# pxx: pot command; sets the throttle input to analog pin Axx; default is A5; both "Axx" and "xx" inputs are valid
# lxx: load command; reads from the load cell; xx sets the extra bits for oversampling; default is 4 (https://en.wikipedia.org/wiki/Oversampling#Resolution)
# exx: escpin command; sets the ESC output pin to digital pin xx; check arduino docs to make sure the chosen pin supports PWM output


def signal_handler(signal, frame):
    global ser
    print('Shutting down, sending STOP command')
    ser.write("s\n".encode('ascii'))
    resp = ser.readline()
    print(resp)
    # ser.write("s\n".encode('ascii'))
    # ser.write("s\n".encode('ascii'))
    print('Done')
    ser.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def since(t0):
    t = time.time()
    dt = t - t0
    ts = f"{dt:.6f}"
    return ts


def expected_time(control_sequence:list):
    total_time = 0
    delay = DEFAULT_DELAY
    for s in control_sequence:
        if s[0] == "D":
            total_time = total_time + float(s[1:])
        elif s[0] == "a":
            total_time = total_time + ARM_DELAY
        elif s[0] == "T":
            T = float(s[1:])
            if T == 0:
                delay = DEFAULT_DELAY
            else:
                delay = T
        else:
            total_time = total_time + delay
    
    return total_time


def ramp(start:int, stop:int, step:int=None, steps:int=None, duration:float=None, interval:float=None):
    # start: int, initial ramp value
    # stop:  int, final ramp value
    # steps: int [optional], single ramp step
    # steps: int [optional], number of ramp steps
    # duration: float [optional], ramp duration in seconds
    # interval: float [optional], interval between each step in seconds
    # NOTE: one and only one between 'step' and 'steps' must be specified
    # NOTE: only one between 'duration' and 'interval' may be specified

    if step is not None and steps is not None or step is None and steps is None:
        raise AttributeError("One and only one between 'step' and 'steps' must be specified!")

    if duration is not None and interval is not None:
        raise AttributeError("Only one between 'step' and 'steps' may be specified!")

    if duration is not None:
        if duration <= 0:
            raise ValueError("Duration must be a positive number!")

    if interval is not None:
        if interval <= 0:
            raise ValueError("Interval must be a positive number!")

    if steps is not None:
        if steps <= 0:
            raise ValueError("Steps must be a positive number!")

    control_sequence = []

    if steps is not None:
        control_step = round(float(stop - start) / steps)
    elif step is not None:
        control_step = step
        # if stop > start:
        #     control_step = step
        # else:
        #     control_step = -step

    if duration is not None:
        if steps is None:
            steps = math.ceil(abs((start - stop) / control_step))
        time_step = duration / steps
        control_sequence.extend([f"T{time_step:.6f}"])
    elif interval is not None:
        time_step = interval
        control_sequence.extend([f"T{time_step:.6f}"])

    control_sequence.extend([f"t{num}" for num in range(start, stop, control_step)])

    # # Before the last step, reset the delay back to the default value
    # control_sequence.extend([f"T0"])

    # Add the last value as a step, because range() skips it
    control_sequence.extend([f"t{stop}"])

    return control_sequence


smooth_ramp = ramp(1100, 1300, step=2)
smooth_ramp_half = ramp(1100, 1500, step=25, duration=10)
smooth_ramp_full = ramp(1100, 2000, step=2, duration=15)
coarse_step = ramp(1100, 1300, step=50, duration=10)
coarse_step_interval = ramp(1300, 1100, step=-50, interval=3)

# NOTE: You can reverse a list using `reversed(input_list)`
# WARNING: Be careful when reversing lists that start with a time interval command!
#          After reverse() the command will be at the end of the list!

# List of strings to send
strings_to_send = ["a"]  # Arm (plus ARM_DELAY)
strings_to_send.extend(smooth_ramp_half)  # Ramp up
strings_to_send.extend(["T0"])  # Reset default interval
strings_to_send.extend(reversed(smooth_ramp))  # Ramp down
strings_to_send.extend(["T0"])  # Reset default interval
strings_to_send.extend(["D2"])  # Pause 2 seconds
strings_to_send.extend(coarse_step)  # Go up in big steps over 10 seconds
# strings_to_send.extend(["T3"])  # Set interval to 3 seconds
strings_to_send.extend(coarse_step_interval)  # Go down in big steps
strings_to_send.extend(["T0"])  # Reset default interval
strings_to_send.extend(["s"])  # Stop


# Open the serial port
# Replace '/dev/ttyACM0' with the actual port name if different
# Adjust the baud rate (e.g., 9600, 115200) as necessary
# ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
ser = serial.Serial('/dev/ttyACM0')

# stty -F /dev/ttyACM0 raw 115200 -iexten -echo -echoe -echok -echoctl -echoke
# stty -F /dev/ttyACM0 raw -iexten -echo -echoe -echok -echoctl -echoke -onlcr
# stty -F /dev/ttyACM0 cs8 9600 ignbrk -brkint -imaxbel -opost -onlcr -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke noflsh -ixon -crtscts
# tail -f /dev/ttyACM0 -s 0.0001 >> test_format5.txt

print(f"Sequence will take ~{expected_time(strings_to_send):.1f}s for {len(strings_to_send)} commands")

t0 = time.time()
delay = DEFAULT_DELAY
# time.sleep(0.6)
# ready = ser.readline()
# print(f"{since(t0)} - {ready}")

# Write each string in the list to the serial port
for string in strings_to_send:
    start = time.time()

    # Use the "T" command to set the delay (in seconds!) between each command in the loop
    if string[0] == "T":
        T = float(string[1:])
        if T == 0.0:
            delay = DEFAULT_DELAY
            print(f"{since(t0)} - Reset delay to default {DEFAULT_DELAY}s")
        else:
            delay = T
            print(f"{since(t0)} - Set delay to {delay}s")
        continue
    
    # Use the "D" command to set a delay (in seconds!) in the loop
    if string[0] == "D":
        D = float(string[1:])
        print(f"{since(t0)} - Delaying for {D}s")
        time.sleep(D)
        continue

    print(f"{since(t0)} - Sending: {string.rstrip()}")
    string = string + "\n" # Always append a newline, to prevent the serial read from going into timeout and get a faster response time
    ser.write(string.encode('ascii'))
    print(f"{since(t0)} - Sent: {string.rstrip()}")
    # ser.flush()
    # WARNING: You MUST read the serial output from the Arduino if you want
    # it to actually execute what you told it to do!
    # Either read the lines from here (don't need to print them out though),
    # OR open the serial monitor in the Arduino IDE/vscode/tty emulator/whatever
    # BUT NEVER OPEN TWO READERS AT THE SAME TIME
    # time.sleep(0.01)
    # if ser.in_waiting > 0:
    # resp = ser.readline()
    # print(f"{since(t0)} -", resp.decode('ascii').rstrip())
    # resp = ser.readlines()
    # for l in resp:
    #     print(f"{since(t0)} -", l.decode('ascii').rstrip())
    # resp = ser.read_until('\n')
    # Sending messages and reading the response takes some time, it makes the timing less accurate

    # If we just sent the arm command, sleep for 'arm_delay' seconds instead of the regular delay
    if string[0] == "a":
        now = time.time()
        if ARM_DELAY - (now - start) > 0:
            # time.sleep(ARM_DELAY - (now - start))
            while ARM_DELAY - (now - start) > 0:
                now = time.time()
        else:
            print(f"{since(start)} - WARNING: loop took {now - start}s, longer than desired delay {ARM_DELAY}s")
        # start = now
    else:
        now = time.time()
        if delay - (now - start) > 0:
            # time.sleep(delay - (now - start))
            while delay - (now - start) > 0:
                now = time.time()
        else:
            print(f"{since(start)} - WARNING: loop took {now - start}s, longer than desired delay {delay}s")
        # start = now

print(f"{since(t0)} - Done")
# Close the serial port
ser.close()
