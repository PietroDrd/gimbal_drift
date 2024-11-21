#undef HID_ENABLED
#include <DueAdcFast.h>
#include "ESC.h"

#define mySerial SerialUSB

DueAdcFast DueAdcF(1024);  // 1024 measures is dimension of internal buffer. (min is 1024)

#define EXTRA_BITS (3) // Extra bits of precision with decimation; MAX 4 if using uint16_t to store values
#define SAMPLES (1<<2*EXTRA_BITS) // 3 extra bits of precision with decimation
#define SAMPLES_NEW (200) // Max ticks to count within a sampling interval
#define LINE_BYTES (16) // Byte length of each output line
#define LINE_BYTES_LC (12) // Byte length of each output line in Load Cell mode
// #define DELTA_T (10) // 10 microeconds
// #define DELTA_T (10 * 1000) // 10 milliseconds
#define DELTA_T_MS (5) // milliseconds
#define DELTA_T (DELTA_T_MS * 1000) // microseconds
volatile uint16_t ticks = 0;
volatile uint16_t ticks_result = 0;
volatile uint32_t times[2] = {0};  // For hall sensor ticks
volatile uint32_t times_result[2] = {0};  // For hall sensor ticks
uint16_t load_cell[SAMPLES] = {0};
uint32_t load_cell_new[SAMPLES_NEW] = {0};
uint32_t avg_load_cell = 0;
uint32_t loops = 0;
uint32_t good_vals = 0;
uint8_t serial_out[LINE_BYTES];

unsigned int ESC_pin = 9;
unsigned int HALL_pin = 50;
unsigned int LOAD_pin = A0;
unsigned int POT_pin;  // DEFAULT POT PIN TO A5
unsigned int pot_value;
unsigned int load_value;
unsigned int now;
unsigned int throttle = 0;
unsigned long lc_extra_bits = 0;
uint32_t lc_samples = 0;
unsigned long start = 0;
unsigned long stop = 0;

// #define SPEED_MIN (1060) // Set the Minimum Speed in microseconds
// #define SPEED_MAX (1860) // Set the Minimum Speed in microseconds
// #define ARM_VAL (500) // Set the Arm Value in microseconds
#define SPEED_MIN (1100) // Set the Minimum Speed in microseconds
#define SPEED_MAX (2000) // Set the Minimum Speed in microseconds
#define ARM_VAL (1000) // Set the Arm Value in microseconds

ESC myESC(ESC_pin, SPEED_MIN, SPEED_MAX, ARM_VAL); // ESC_Name (PIN, Minimum Value, Maximum Value, Arm Value)

String command;
const char arm_command = 'a';
const char thr_command = 't';
const char pot_command = 'p';
const char load_command = 'l';
const char stop_command = 's';
const char calib_command = 'c';
const char escpin_command = 'e';
const char nothing_to_do = (char)0;
char cmd = nothing_to_do;  // Default command on first start
bool print_thr = true;
bool pot_on = false;
String thr_str;
String pot_str;


// these 3 lines of code are essential for the functioning of the library
// you don't call ADC_Handler.
// is used automatically by the PDC every time it has filled the buffer
// and rewrite buffer.
void ADC_Handler() {
  DueAdcF.adcHandler();
}

void mydelay(unsigned long interval){
    unsigned int a = micros();
    unsigned int b = micros();
    while (b - a < interval) {
        b = micros();
    }
}

void got_tick() {
  ticks++;
  times[1] = micros();
}

void measure_and_print_rpm() {
  loops = 0;
  avg_load_cell = 0;
  // memset(load_cell, 0, sizeof(load_cell)); // Clear the array!
  memset(load_cell_new, 0, sizeof(load_cell_new)); // Clear the array!
  times[0] = micros(); // Start time
  times[1] = micros(); // End time
  now = times[1];
  ticks = 0; // Reset the value just before entering the loop
  // WARNING: This code assumes that we can get at least #SAMPLES before we exit the loop
  // If we don't, then some of the load cell readings will still be 0
  // while ((times[1] - times[0] < DELTA_T) || (ticks == 0 && (times[1] - times[0] < 2*DELTA_T))) {
  // Keep collecting samples in a fixed size buffer, and overwrite them if we exceed its size
  // Note: we assume that we'll be able to collect more than SAMPLES values before we pass DELTA_T
  // while ((now - times[0] < DELTA_T) || (ticks == 0 && (now - times[0] < 2*DELTA_T))) {
  //   // NOTE: if we loop more than #SAMPLES times, we'll overwrite some values
  //   load_cell[loops % SAMPLES] = DueAdcF.ReadAnalogPin(LOAD_pin);
  //   // times[1] = micros();
  //   now = micros();
  //   loops++;
  // }
  // Collect SAMPLES values for each element of the array, then move forward to the next item.
  // For each item that has collected all the samples, we can apply decimation.
  // If we have more than one "full" value after decimation, we average the decimated values.
  // If not, should we just do averaging? WARNING: how do we deal with the different number of bits?
  // Note: the buffer of values must be bigger than the maximum number of (decimated)
  // samples we can expect to collect in our DELTA_T
  while ((now - times[0] < DELTA_T) || (ticks == 0 && (now - times[0] < 2*DELTA_T))) {
    // NOTE: integer division on the index
    // Collect SAMPLES values for each item, so we can apply decimation to them
    load_cell_new[loops / SAMPLES] += DueAdcF.ReadAnalogPin(LOAD_pin);
    // times[1] = micros();
    now = micros();
    loops++;
  }
  ticks_result = ticks; // Store the result asap to avoid more increments while preparing the printout
  times_result[1] = times[1]; // Save the end value first, since it has more chance of getting updated
  times_result[0] = times[0];
  good_vals = loops / SAMPLES;
  // for (uint32_t i=0; i<min(loops, SAMPLES); i++) {
  // for (uint32_t i=0; i<(loops / SAMPLES); i++) {
  for (uint32_t i=0; i<min(good_vals, SAMPLES_NEW); i++) {
    avg_load_cell += load_cell_new[i] >> EXTRA_BITS;
  }
  // avg_load_cell = avg_load_cell >> EXTRA_BITS; // Decimation
  // avg_load_cell = avg_load_cell / SAMPLES; // Averaging
  // avg_load_cell = avg_load_cell / min(loops, SAMPLES); // Averaging
  // avg_load_cell = avg_load_cell / good_vals; // Averaging
  avg_load_cell = avg_load_cell / min(good_vals, SAMPLES_NEW); // Averaging
  (uint16_t &)serial_out[0] = (uint16_t)throttle;
  (uint32_t &)serial_out[2] = (uint32_t)times[0]; // Start time
  (uint16_t &)serial_out[6] = (uint16_t)ticks_result; // Ticks
  (uint32_t &)serial_out[8] = (uint32_t)times[1]; // End time
  (uint32_t &)serial_out[12] = (uint32_t)avg_load_cell; // Load Cell
  mySerial.write((char *)serial_out, LINE_BYTES);
}

void setup() {
  mySerial.begin(115200);  // opens serial port, sets data rate to 115200 bps
  while (!mySerial);  // Wait for serial to initialize
  // mySerial.setTimeout(10);  // Set timeout to 10ms to waste less time when reading serial input
  String rdy = "Arduino is ready! ";
  rdy.concat(millis());
  rdy.concat("ms\n");
  mySerial.print(rdy);
  // https://github.com/AntonioPrevitali/DueAdcFast/blob/main/examples/Sample3/Sample3.pde
  // analogReadResolution(12);
  DueAdcF.EnablePin(LOAD_pin);  // Load cell (A0)
  // DueAdcF.EnablePin(POT_pin);  // Throttle Pot // This is useless without a predefined value!
  DueAdcF.Start1Mhz();       // max speed 1Mhz (sampling rate)
  // DueAdcF.Start(255);        // with prescaler value form 3 to 255.
                             // 255 is approx. 7812 Hz (sampling rate)
  // https://www.arduino.cc/reference/en/language/functions/external-interrupts/attachinterrupt/
  // attachInterrupt(pin, ISR, mode)
  // pinMode(HALL_pin, INPUT_PULLUP);
  pinMode(HALL_pin, INPUT);
  attachInterrupt(HALL_pin, got_tick, CHANGE);
}

void loop() {  
  while (mySerial.available() == 0) {
    switch (cmd)
    {
    case arm_command:
      myESC.arm(); // Send the Arm value
      // mySerial.println("Sending ARM command");
      (uint32_t &)serial_out[0] = (uint32_t)0xffff; // "Not a throttle line"
      (uint32_t &)serial_out[4] = (uint32_t)0xfff1; // "Sending ARM command"
      (uint32_t &)serial_out[8] = (uint32_t)0xfff1; // "Sending ARM command"
      (uint32_t &)serial_out[12] = (uint32_t)0xffff; // (End of line)
      mySerial.write((char *)serial_out, LINE_BYTES);
      cmd = nothing_to_do;
      break;
    case thr_command:
      if (print_thr) {
        // thr_str = "Set throttle to ";
        // thr_str.concat(throttle);
        // thr_str.concat('\n');
        // mySerial.print(thr_str);
        (uint32_t &)serial_out[0] = (uint32_t)0xffff; // "Not a throttle line"
        (uint16_t &)serial_out[4] = (uint16_t)0xfff2; // "Set throttle to "
        (uint16_t &)serial_out[6] = (uint16_t)throttle; // Throttle value
        (uint16_t &)serial_out[8] = (uint16_t)0xfff2; // "Set throttle to "
        (uint16_t &)serial_out[10] = (uint16_t)throttle; // Throttle value
        (uint32_t &)serial_out[12] = (uint32_t)0xffff; // (End of line)
        mySerial.write((char *)serial_out, LINE_BYTES);
        print_thr = false;
      }
      myESC.speed(throttle); // sets the ESC speed according to the scaled value
      measure_and_print_rpm();
      // cmd = nothing_to_do;
      break;
    case pot_command:
      pot_value = DueAdcF.ReadAnalogPin(POT_pin);
      throttle = map(pot_value, 0, 4095, SPEED_MIN, SPEED_MAX);
      // throttle = map(pot_value, 0, 4095, SPEED_MIN, 1300); // Limit throttle
      // if (print_thr) {
      //   thr_str = "Set throttle to ";
      //   thr_str.concat(throttle);
      //   thr_str.concat('\n');
      //   mySerial.print(thr_str);
      //   print_thr = false;
      // }
      // throttle = 1150;
      // pot_str = "Pin ";
      // pot_str.concat(POT_pin);
      // pot_str.concat(" - Set throttle to ");
      // pot_str.concat(throttle);
      // mySerial.println(pot_str);
      myESC.speed(throttle); // sets the ESC speed according to the scaled value
      measure_and_print_rpm();
      break;
    case load_command:
      if (print_thr) {
        // mySerial.print("Reading LOAD CELL\n");
        (uint32_t &)serial_out[0] = (uint32_t)0xffff; // "Not a throttle line"
        (uint32_t &)serial_out[4] = (uint32_t)0xfffc; // "Reading LOAD CELL"
        (uint32_t &)serial_out[8] = (uint32_t)0xfffc; // "Reading LOAD CELL"
        (uint32_t &)serial_out[12] = (uint32_t)0xffff; // (End of line)
        mySerial.write((char *)serial_out, LINE_BYTES);
        print_thr = false;
      }
      avg_load_cell = 0;
      times[0] = micros();
      for (uint32_t i=0; i<lc_samples; i++) {
        avg_load_cell += DueAdcF.ReadAnalogPin(LOAD_pin);
      }
      times[1] = micros();
      avg_load_cell = avg_load_cell >> lc_extra_bits; // Decimation
      (uint32_t &)serial_out[0] = (uint32_t)0xfcfffcff; // This is a load cell reading!
      (uint32_t &)serial_out[4] = (uint32_t)times[0]; // Start time
      (uint32_t &)serial_out[8] = (uint32_t)avg_load_cell; // Load Cell
      (uint32_t &)serial_out[12] = (uint32_t)times[1]; // End time
      mySerial.write((char *)serial_out, LINE_BYTES);
      break;
    case stop_command:
      myESC.stop(); // Send the Stop value
      // mySerial.println("Sending STOP command");
      (uint32_t &)serial_out[0] = (uint32_t)0xffff; // "Not a throttle line"
      (uint32_t &)serial_out[4] = (uint32_t)0xfff0; // "Sending STOP command"
      (uint32_t &)serial_out[8] = (uint32_t)0xfff0; // "Sending STOP command"
      (uint32_t &)serial_out[12] = (uint32_t)0xffff; // (End of line)
      mySerial.write((char *)serial_out, LINE_BYTES);
      cmd = nothing_to_do;
      break;
    case calib_command:
      myESC.calib(); // Calibrate
      mySerial.println("Throttle calibration");
      // cmd = arm_command; // Arm after calibration?
      cmd = nothing_to_do;
      break;
    case escpin_command:
      if (ESC_pin > 1 && ESC_pin <= NUM_DIGITAL_PINS) {
        mySerial.print("Setting ESC to pin ");
        mySerial.println(ESC_pin);
        cmd = nothing_to_do;
      } else {
        mySerial.print("WARNING: Invalid ESC pin ");
        mySerial.println(ESC_pin);
        cmd = nothing_to_do;
      }
      break;
    case nothing_to_do:
      if (print_thr) {
        mySerial.println("Nothing to do");
        print_thr = false;
      }
      break;
    default:
      String resp = "Unrecognized command, doing nothing! cmd = '";
      resp.concat(command);
      mySerial.println(resp);
      break;
    }
    // delay(5);
  }

  command = mySerial.readStringUntil('\n'); // Note: the '\n' character is discarded from the serial buffer
  command.trim();
  unsigned int cmdlen = command.length();
  cmd = command.charAt(0);  // Warning: this limits the commands to a single character (one byte)

  // Warning: this matches the beginning of the string - there are no safety checks for what comes after!
  // Eg. by typing "as", this will match the arm command "a", becaues the input starts with "a"
  if (command.startsWith(String(arm_command))) {
    // cmd = arm_command;
  } else if (command.startsWith(String(thr_command))) {
    print_thr = true;
    if (cmdlen > 1 && cmdlen < 6) { // match "t0" - "t1024"
      throttle = command.substring(1).toInt();
      // If we have previously enabled the POT_pin, we must disable it
      if (pot_on == true) {
        DueAdcF.Stop();
        DueAdcF.DisEnabPin();
        DueAdcF.EnablePin(LOAD_pin);  // Load Cell Pin
        DueAdcF.Start1Mhz();
        pot_on = false;
      }
    } else {
      cmd = nothing_to_do;
    }
    // cmd = thr_command;
  } else if (command.startsWith(String(pot_command))) {
    // Changing active ADC pins: first stop the ADC, then disable all pins, then enable the new pins, and restart the ADC
    DueAdcF.Stop();
    DueAdcF.DisEnabPin();
    // print_thr = true;
    // POT_pin = A5; // DEFAULT POT PIN TO A5
    // "pa0"
    if (cmdlen > 1) {
      String pot_str = command.substring(1);  // Assume there is no space after the 'p'
      pot_str.toLowerCase();
      // TODO: Maybe implement a bounds check? E.g. if we know pin A75 doesn't exist, skip the command
      // Analog pins "a0" - "a7" for stuff like Arduino Uno, or "a11" for the Arduino Giga R1
      // https://github.com/arduino/ArduinoCore-avr/blob/master/variants/standard/pins_arduino.h#L28-L72
      // https://github.com/arduino/ArduinoCore-mbed/blob/main/variants/GIGA/pins_arduino.h#L21-L56
      // POT_pin = NUM_DIGITAL_PINS - NUM_ANALOG_INPUTS + analog_pin_num;
      if (pot_str.startsWith("a")) {
        POT_pin = A0 + pot_str.substring(1).toInt();;
      } else if (isDigit(pot_str[0])) {
        POT_pin = A0 + pot_str.substring(0).toInt();
      }
    } else {
      POT_pin = A5; // DEFAULT POT PIN TO A5
    }
    DueAdcF.EnablePin(POT_pin);  // Throttle Pot
    DueAdcF.EnablePin(LOAD_pin);  // Load Cell Pin
    DueAdcF.Start1Mhz();
    pot_on = true;  // Set the flag - the ADC is running with the pot pin enabled
    // cmd = pot_command;
  } else if (command.startsWith(String(load_command))) {
    print_thr = true;
    // Note: adding N extra bits of precision requires 4^N samples, thus
    // reducing the sampling rate by 4^N.
    // We set the ADC to run in 12 bit mode, which means we could add up to
    // 20/2=10 extra bits if we store the result in a uint32_t (because we'd
    // need another 4^10=2^20 extra samples, each sample is 12 bits, and
    // 2**12 * 2**20 = 2**32 so we could overflow if we try to add more).
    if (cmdlen > 0 && cmdlen < 4) { // match "l" or "l0" - "l10"
      if (cmdlen > 1) { // match "l0" - "l10"
        lc_extra_bits = command.substring(1).toInt();
        if (lc_extra_bits > 10) {
          lc_extra_bits = 10;
        }
      } else {
        lc_extra_bits = 4;
      }
      lc_samples = (1<<2*lc_extra_bits);
      // If we have previously enabled the POT_pin, we must disable it
      if (pot_on == true) {
        DueAdcF.Stop();
        DueAdcF.DisEnabPin();
        DueAdcF.EnablePin(LOAD_pin);  // Load Cell Pin
        DueAdcF.Start1Mhz();
        pot_on = false;
      }
    } else {
      cmd = nothing_to_do;
    }
    // cmd = load_command;
  } else if (command.startsWith(String(stop_command))) {
    // cmd = stop_command;
  } else if (command.startsWith(String(calib_command))) {
    // cmd = calib_command;
  } else if (command.startsWith(String(escpin_command))) {
    // myESC.~ESC();
    // Warning: no error checking. If the string is invalid, this will return 0
    // and it will be rejected in the loop
    ESC_pin = command.substring(1).toInt();
    myESC = ESC(ESC_pin, SPEED_MIN, SPEED_MAX, ARM_VAL); // ESC_Name (PIN, Minimum Value, Maximum Value, Arm Value)
  } else {
    // cmd = wrong_command;
  }
}
