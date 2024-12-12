#include <Servo.h>

#define SPEED_MIN (1100)                                  // Set the Minimum Speed in microseconds
#define SPEED_MAX (2000)
#define ARM_VAL (1000)                                    // Set the Arm Value in microseconds

Servo ESC1;
Servo ESC2;
Servo ESC3;
Servo ESC4;

int motor1 = 0, motor2 = 0, motor3 = 0, motor4 = 0;
int numValues = 0;

void setup() {
    ESC1.attach(3,1000,2000);
    ESC2.attach(5,1000,2000);
    ESC3.attach(6,1000,2000);
    ESC4.attach(9,1000,2000);
    Serial.begin(115200);
}

void loop() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n'); // Read until newline
        if (command == "A") { // Arm command
            //esc1.arm();
            //esc2.arm();
            //esc3.arm();
            //esc4.arm();
            //Serial.println("Motors armed.");
        } else if (command == "S") { // Stop command
            ESC1.write(1000); // PWM signal to stop
            ESC2.write(1000);
            ESC3.write(1000);
            ESC4.write(1000);
            Serial.println("Motors stopped.");
        } // Ensure the command contains motor values
            
            
            // Parse the motor values from the command string
            numValues = sscanf(command.c_str(), "%d,%d,%d,%d", &motor1, &motor2, &motor3, &motor4);
            // Check if we successfully parsed all four values
            
    }
    while(Serial.available() == 0){
        if (numValues > 0) {
                    // Set the speed for each motor
                    ESC1.write(motor1);
                    ESC2.write(motor2);
                    ESC3.write(motor3);
                    ESC4.write(motor4);
                    // Provide feedback
                    Serial.print("Motor values: ");
                    Serial.print(motor1);
                    Serial.print(", ");
                    Serial.print(motor2);
                    Serial.print(", ");
                    Serial.print(motor3);
                    Serial.print(", ");
                    Serial.println(motor4);
                    delayMicroseconds(1000);
            }
    }
    
}
