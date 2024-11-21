# DRIFT

## TLDR When running

```bash
# For the Arduino Due, Native USB port
stty -F /dev/ttyACM0 raw -iexten -echo -echoe -echok -echoctl -echoke
# For the Arduino Uno
stty -F /dev/ttyACM0 cs8 115200 ignbrk -brkint -imaxbel -opost -onlcr -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke noflsh -ixon -crtscts
# Log output to file
cat /dev/ttyACM0 >> test_format5.txt
tail -f /dev/ttyACM0 -s 0.0001 >> test_format5.txt
```

## Arduino setup

Install the following Arduino libraries:

```
Servo
RC_ESC
DueAdcFast
```

Then, open `drift.ino`, compile it, and upload it to the board.

To see what is going on and send inputs manually, open the Serial Monitor (baud rate `115200`)

## Python setup

Create a virtual environment with pip, then activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required packages (make sure the virtualenv is active!):

```bash
pip install -r requirements.txt
```

Then, run the script:

```bash
python control.py
```

## Running

**IMPORTANT**: When the Arduino board writes to serial, you MUST read it as soon as possible. If you don't, the Arduino will most likely not execute commands as expected. This is due to the way `Serial.available()` (at the beginning of the loop in `drift.ino`) works.

There are a few ways to do this:

- Using the Serial Monitor in the Arduino IDE or VSCode
  - This works fine, because serial output is always being read. The ESC will never actually go to the "inactive".
  - This should work well on all operating systems
  - NOTE: if you want to manually send commands to the Arduino from the serial monitor, make sure you select `LF` **line endings**. This will allow the Arduino to read and execute your command immediately, instead of waiting for the `Serial.readStringUntil()` function to time out
- Using the terminal:
  - First, if you're on Linux/Mac, run this to ensure that the output is read correctly at full speed:
    - For the Arduino Due: `stty -F /dev/ttyACM0 raw -iexten -echo -echoe -echok -echoctl -echoke -onlcr`
    - For the Arduino Uno: `stty -F /dev/ttyACM0 cs8 115200 ignbrk -brkint -imaxbel -opost -onlcr -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke noflsh -ixon -crtscts`
    - Replace `/dev/ttyACM0` with whatever serial port you're actually using
  - Then, you can use one of the two following commands to read the serial output:
    - `cat /dev/ttyACM0` <- this is preferable, especially for the Due Native USB port (but sometimes doesn't work as expected?)
    - `tail -f /dev/ttyACM0 -s 0.001` <- make sure you specify a fast refresh interval (`-s 0.001` will refresh every ~1ms). Otherwise the Arduino's send buffer gets filled and things may not work properly (and the output will be all messed up)
  - You can save the output directly into a file: `cat /dev/ttyACM0 >> run.log`
  - Note: this assumes that the Arduino is connected to the `/dev/ttyACM0` port on Linux/MacOS. On Windows, it should be called `COMx` (e.g. `COM1`)
- Using the `ser.readline()` function directly in the python script
  - [Documentation](https://pyserial.readthedocs.io/en/latest/shortintro.html#readline)
  - Works ok, but you need to know ahead of time what output to expect from the arduino and program your script accordingly. If you're not "in sync" with the Arduino (e.g. you expect a message but the Arduino is in a different state so it will never come) then the script could get stuck, or the Arduino might behave erratically 
  - TODO: check out `serial.tools.miniterm`
  
You can also manually send commands from a terminal like this: `echo "t1000" > /dev/ttyACM0` (this will set the throttle to 1000). Note that this command only *writes* to serial, so you still nead something to read the serial response (either in another terminal, or the Serial Monitor in VSCode/Arduino IDE).

## Notes and links

- The **Servo library** supports up to 12 motors on most Arduino boards and 48 on the Arduino Mega. On boards other than the Mega, **use of the library disables `analogWrite()` (PWM) functionality on pins 9 and 10, whether or not there is a Servo on those pins**. On the Mega, up to 12 servos can be used without interfering with PWM functionality; **use of 12 to 23 motors will disable PWM on pins 11 and 12**. ([source](https://www.arduino.cc/reference/en/libraries/servo/))

### Arduino **Giga**
- "It should be noted that the internal **operating voltage of the microcontroller is 3.3V**, and you should not apply voltages higher than that to the GPIO pins." ([source](https://docs.arduino.cc/tutorials/giga-r1-wifi/cheat-sheet/#power-supply))
- As the Arduino Mbed OS GIGA Board Package is based on MbedOS, it is possible for the operating system to crash while running a sketch.  
On most Arduino boards, when a sketch fails due to e.g. memory shortage, the board resets.  
On the GIGA R1, **whenever the MbedOS fails, the board does not reset automatically**. Instead, if it fails, the onboard red LED will start to blink in a looping pattern of 4 fast blinks and 4 slow blinks.  
In case you encounter the red LED, you can either:
  - Press the reset button once (this resets the sketch).
  - Double-tap the reset button to enter bootloader mode (allowing you to re-program the board). ([source](https://docs.arduino.cc/tutorials/giga-r1-wifi/cheat-sheet/#mbed-os))
- The GIGA R1 has 12 PWM capable pins, the PWM capable pins are 2-13. ([source](https://docs.arduino.cc/tutorials/giga-r1-wifi/cheat-sheet/#pwm-pins))