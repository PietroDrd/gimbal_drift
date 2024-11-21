#define MOTOR_PIN_1 2
#define MOTOR_PIN_2 3
#define MOTOR_PIN_3 4
#define MOTOR_PIN_4 5

#define DSHOT600_HIGH 1250   // High time for DSHOT600 (in nanoseconds)
#define DSHOT600_LOW  625   // Low time for DSHOT600 (in nanoseconds)
#define DSHOT_BIT_TIME 1670 // Total bit time for DSHOT600 (in nanoseconds)

// Function to send a DSHOT frame to a motor
void sendDShot(int pin, int throttleValue) {
  uint16_t packet = throttleValue << 1;  // Shift the throttle value left by 1 to make space for the checksum
  packet |= calculateChecksum(throttleValue);  // Add the checksum

  for (int i = 15; i >= 0; i--) {
    if (packet & (1 << i)) {
      // Send a '1'
      digitalWrite(pin, HIGH);
      delayMicroseconds(DSHOT600_HIGH);
      digitalWrite(pin, LOW);
      delayMicroseconds(DSHOT_BIT_TIME - DSHOT600_HIGH);
    } else {
      // Send a '0'
      digitalWrite(pin, HIGH);
      delayMicroseconds(DSHOT600_LOW);
      digitalWrite(pin, LOW);
      delayMicroseconds(DSHOT_BIT_TIME - DSHOT600_LOW);
    }
  }
}

// Calculate a simple checksum (XOR of nibbles)
uint8_t calculateChecksum(uint16_t value) {
  uint8_t checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0x0F;
  return checksum;
}

void setup() {
  Serial.begin(115200);

  // Initialize the motor pins
  pinMode(MOTOR_PIN_1, OUTPUT);
  pinMode(MOTOR_PIN_2, OUTPUT);
  pinMode(MOTOR_PIN_3, OUTPUT);
  pinMode(MOTOR_PIN_4, OUTPUT);

  // Wait a bit to allow the ESC to complete the initial beeps
  delay(2000);

}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read until newline
        if (command == "A") { // Arm command
            sendDShot(MOTOR_PIN_1, 0);
            sendDShot(MOTOR_PIN_2, 0);
            sendDShot(MOTOR_PIN_3, 0);
            sendDShot(MOTOR_PIN_4, 0);
            delay(100); // Short delay to ensure the ESCs register the arming signal
            sendDShot(MOTOR_PIN_1, 1000);
            sendDShot(MOTOR_PIN_2, 1000); 
            sendDShot(MOTOR_PIN_3, 1000);
            sendDShot(MOTOR_PIN_4, 1000);
            Serial.println("Motors armed.");
        } else if (command == "S") { // Stop command
            // Send a zero throttle signal to arm the ESC
            sendDShot(MOTOR_PIN_1, 1000);
            sendDShot(MOTOR_PIN_2, 1000);
            sendDShot(MOTOR_PIN_3, 1000);
            sendDShot(MOTOR_PIN_4, 1000);
            Serial.println("Motors stopped.");
        } // Ensure the command contains motor values
    int motor1 = 0, motor2 = 0, motor3 = 0, motor4 = 0;
            
    // Parse the motor values from the command string
    int numValues = sscanf(command.c_str(), "%d,%d,%d,%d", &motor1, &motor2, &motor3, &motor4);
    // Send throttle values to the motors
    if (numValues == 4) {
      // Set the speed for each motor
      sendDShot(MOTOR_PIN_1, motor1);
      sendDShot(MOTOR_PIN_2, motor2);
      sendDShot(MOTOR_PIN_3, motor3);
      sendDShot(MOTOR_PIN_4, motor4);

      // Provide feedback
      //Serial.print("Motor values: ");
      Serial.print(motor1);
      Serial.print(", ");
      Serial.print(motor2);
      Serial.print(", ");
      Serial.print(motor3);
      Serial.print(", ");
      Serial.println(motor4);
    }
  }
}
