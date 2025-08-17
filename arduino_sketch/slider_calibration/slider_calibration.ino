#include <AccelStepper.h>

// --- Hardware pin setup ---

const int stepPin = 3;
const int dirPin = 2;
const int limitHomePin = 4; // Home position switch
const int stepsPerCM = 50; // <-- Calibrate for your hardware

AccelStepper stepper(AccelStepper::DRIVER, stepPin, dirPin);

// --- Movement Variables ---
int roundCount = 0;                // Tracks how many rounds completed
const int cellSizesCM[] = {4, 6, 8, 10};        // Each cell is 5 cm wide
const int scanningAreaCM = 35;     // Fixed position for scanning area
const int sortedAreaStartCM = 50;  // Sorted area starts at 50 cm

void setup() {
  Serial.begin(9600);
  pinMode(limitHomePin, INPUT_PULLUP);

  stepper.setMaxSpeed(800);
  stepper.setAcceleration(400);

  homeStepper();
  Serial.println("Ready for input! Enter cell (a-d) to start a round.");
}

void loop() {
  if (Serial.available()) {
    char input = Serial.read();
    input = tolower(input); // Accept uppercase
    if (input >= 'a' && input <= 'd') {
      int cellCM = (input - 'a' + 1) * cellWidthCM;
      Serial.print("Moving to cell ");
      Serial.print(input);
      Serial.print(" at ");
      Serial.print(cellCM);
      Serial.println(" cm");

      // Move to chosen cell
      moveToPosition(cellCM);
      delay(200);

      // Move to scanning area
      Serial.print("Moving to Scanning Area (");
      Serial.print(scanningAreaCM);
      Serial.println(" cm)");
      moveToPosition(scanningAreaCM);
      delay(200);

      // Calculate sorted area position for this round
      int sortedAreaCM = sortedAreaStartCM + roundCount * cellWidthCM;
      Serial.print("Moving to Sorted Area (");
      Serial.print(sortedAreaCM);
      Serial.println(" cm)");
      moveToPosition(sortedAreaCM);
      delay(200);

      // Record round completion
      roundCount++;
      Serial.print("Round completed! Sorted area for next round: ");
      Serial.print(sortedAreaStartCM + roundCount * cellWidthCM);
      Serial.println(" cm");

      // Return to home
      Serial.println("Returning Home...");
      moveToPosition(0);

      Serial.println("Ready for next input (a-d).");
    } else {
      Serial.println("Invalid input. Please enter a, b, c, or d.");
    }
    // Flush any extra input
    while (Serial.available()) Serial.read();
  }
}

// --- Homing routine ---
void homeStepper() {
  Serial.println("Homing...");
  stepper.setSpeed(-400);
  while (digitalRead(limitHomePin) == HIGH) {
    stepper.runSpeed();
  }
  stepper.stop();
  stepper.setCurrentPosition(0);
  Serial.println("Stepper homed to position 0cm.");
}

// --- Move to position in cm from home ---
void moveToPosition(int cm) {
  long targetSteps = cm * stepsPerCM;
  stepper.moveTo(targetSteps);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }
  Serial.print("Arrived at ");
  Serial.print(cm);
  Serial.println(" cm.");
}