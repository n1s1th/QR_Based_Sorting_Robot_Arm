#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <AccelStepper.h>

// --- Robot Arm Setup ---
Adafruit_PWMServoDriver srituhobby = Adafruit_PWMServoDriver();
#define NUM_SERVOS 6
#define servoMIN 150 //0
#define servoMAX 600 // 180
int defaultPulse[NUM_SERVOS] = {200, 320, 420, 150, 150, 220};
int currentPulse[NUM_SERVOS] = {200, 320, 420, 170, 180, 220};
int stepDelay = 20;
int stepSize = 2;

// --- Stepper/Slider Setup ---
const int stepPin = 3;
const int dirPin = 2;
const int limitHomePin = 4;
const int MS1 = 9;
const int MS2 = 10;
const int stepsPerCM = 50*8; // 50 steps per cm, 8 microsteps per step
AccelStepper stepper(AccelStepper::DRIVER, stepPin, dirPin);

// --- Movement Variables ---
int roundCount_b1 = 0;
int roundCount_b2 = 0;
int roundCount_b3 = 0;
int roundCount_b4 = 0;
const int cellSizesCM[] = {8, 17, 26, 30}; // Example: 'A'=8cm, 'B'=14cm, 'C'=22cm, 'D'=25cm
const int numCells = sizeof(cellSizesCM) / sizeof(cellSizesCM[0]);
const int scanningAreaCM = 38;
const int cellWidthCMSorted = 7;

// --- Serial Input State ---
String sliderInput = "";
String robotInput = "";
String sortInput = "";
bool waitingForInitialInputs = true;
bool waitingForSortInput = false;

// --- SETUP ---
void setup() {
  Serial.begin(9600);
  pinMode(limitHomePin, INPUT_PULLUP);

  srituhobby.begin();
  srituhobby.setPWMFreq(60);
  setServos(defaultPulse);

  pinMode(MS1, OUTPUT); // Setup Microstepping pins
  pinMode(MS2, OUTPUT);

  digitalWrite(MS1, HIGH); // Set to 1/8 microstepping
  digitalWrite(MS2, HIGH);

  stepper.setMaxSpeed(800*8);
  stepper.setAcceleration(400*8);
  homeStepper();

  Serial.println("Enter slider position and robot arm action separated by space, e.g.: B c");
}

// --- LOOP ---
void loop() {
  if (waitingForInitialInputs && Serial.available() > 0) {
    String inStr = Serial.readStringUntil('\n');
    inStr.trim();
    int spaceIdx = inStr.indexOf(' ');
    // No input validation! Assumes input is always correct format.
    sliderInput = inStr.substring(0, spaceIdx);
    robotInput = inStr.substring(spaceIdx+1);

    waitingForInitialInputs = false;

    // --- Workflow Update ---
    // 1. Move slider to selected position
    int cellIndex = sliderInput[0] - 'A';
    int cellCM = cellSizesCM[cellIndex];
    Serial.print("Moving slider to cell ");
    Serial.print(sliderInput);
    Serial.print(" at ");
    Serial.print(cellCM);
    Serial.println(" cm");
    moveToPosition(cellCM);

    // 2. Trigger robot arm function
    Serial.print("Triggering robot arm function: ");
    Serial.println(robotInput);
    dispatchFunction(robotInput[0]);

    // 3. Move slider to scanningAreaCM
    Serial.print("Moving slider to scanning area (");
    Serial.print(scanningAreaCM);
    Serial.println(" cm)");
    moveToPosition(scanningAreaCM);

    // 4. Trigger scanningdrop
    Serial.println("Triggering scanningdrop()");
    scanningdrop();

    // 5. Send READY_TO_SCAN signal to Python
    Serial.println("READY_TO_SCAN");

    // Prepare for sort input
    waitingForSortInput = true;
    Serial.println("Enter sorted area action (b1, b2, b3):");
  }
  else if (waitingForSortInput && Serial.available() > 0) {
    String inStr = Serial.readStringUntil('\n');
    inStr.trim();
    // No input validation! Assumes sort input always correct.
    sortInput = inStr;

    // --- Workflow Update ---
    // 1. Trigger scanningpick
    Serial.println("Triggering scanningpick()");
    scanningpick();

    // 2. Sorted area function
    triggerSortFunction(sortInput);

    // 3. Send ROUND_COMPLETE signal to Python
    Serial.println("ROUND_COMPLETE");

    // 4. Return slider to home position
    Serial.println("Returning slider to home position...");
    homeStepper();

    // Prepare for next round
    waitingForInitialInputs = true;
    waitingForSortInput = false;
    Serial.println("Enter slider position and robot arm action separated by space, e.g.: B c");
  }
}

// --- Sorted Area Functions ---
void sortedAreaCM1() {
  int sortedAreaStartCM = 55;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b1 * cellWidthCMSorted;
  Serial.print("Moving slider to sorted area for b1 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b1();
  roundCount_b1++;
}
void sortedAreaCM2() {
  int sortedAreaStartCM = 55;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b2 * cellWidthCMSorted;
  Serial.print("Moving slider to sorted area for b2 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b2();
  roundCount_b2++;
}
void sortedAreaCM3() {
  int sortedAreaStartCM = 70;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b3 * cellWidthCMSorted;
  Serial.print("Moving slider to sorted area for b3 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b3();
  roundCount_b3++;
}
void sortedAreaCM4() {
  int sortedAreaStartCM = 70;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b4 * cellWidthCMSorted;
  Serial.print("Moving slider to sorted area for b4 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b4();
  roundCount_b4++;
}

// --- Robot Arm Functions ---
// ... (unchanged, same as your code)
void setServos(const int pulses[NUM_SERVOS]) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    srituhobby.setPWM(i, 0, pulses[i]);
    currentPulse[i] = pulses[i];
  }
}
void moveServosSmooth(const int fromPulses[NUM_SERVOS], const int toPulses[NUM_SERVOS]) {
  int localCurrent[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++) localCurrent[i] = fromPulses[i];
  int maxSteps = 0;
  int delta[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++) {
    delta[i] = abs(toPulses[i] - fromPulses[i]);
    if (delta[i] > maxSteps) maxSteps = delta[i];
  }
  if (maxSteps == 0) maxSteps = 1;
  maxSteps = maxSteps / stepSize;
  for (int s = 0; s <= maxSteps; s++) {
    int newPulse[NUM_SERVOS];
    for (int i = 0; i < NUM_SERVOS; i++) {
      if (localCurrent[i] < toPulses[i]) {
        localCurrent[i] = min(localCurrent[i] + stepSize, toPulses[i]);
      } else if (localCurrent[i] > toPulses[i]) {
        localCurrent[i] = max(localCurrent[i] - stepSize, toPulses[i]);
      }
      newPulse[i] = localCurrent[i];
    }
    setServos(newPulse);
    delay(stepDelay);
  }
  setServos(toPulses);
  for (int i = 0; i < NUM_SERVOS; i++) currentPulse[i] = toPulses[i];
}
void robotarm(const int upperPulses[NUM_SERVOS], const int targetPulses[NUM_SERVOS], const int targetPulsesClose[NUM_SERVOS], const int upperPulsesClose[NUM_SERVOS]) {
  moveServosSmooth(currentPulse, upperPulses);
  delay(1000);
  moveServosSmooth(upperPulses, targetPulses);
  delay(1000);
  moveServosSmooth(targetPulses, targetPulsesClose);
  delay(1000);
  moveServosSmooth(targetPulsesClose, upperPulsesClose);
  delay(1000);
  moveServosSmooth(upperPulsesClose, defaultPulse);
  delay(1000);
}

void scanning(const int upperPulses[NUM_SERVOS], const int targetPulses[NUM_SERVOS], const int targetPulsesClose[NUM_SERVOS], const int upperPulsesClose[NUM_SERVOS]) {
  moveServosSmooth(currentPulse, upperPulses);
  delay(1000);
  moveServosSmooth(upperPulses, targetPulses);
  delay(1000);
  moveServosSmooth(targetPulses, targetPulsesClose);
  delay(1000);
  moveServosSmooth(targetPulsesClose, upperPulsesClose);
  delay(1000);
}

void a() {
  int upperPulses[NUM_SERVOS]      = {350, 180, 420, 220, 450, 240};
  int targetPulses[NUM_SERVOS]     = {350, 270, 420, 440, 520, 245};
  int targetPulsesClose[NUM_SERVOS]= {170, 270, 420, 440, 520, 245};
  int upperPulsesClose[NUM_SERVOS] = {170, 230, 420, 400, 560, 245};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}

void b(){
  int upperPulses[NUM_SERVOS]      = {350, 270, 390, 180, 250, 230};
  int targetPulses[NUM_SERVOS]     = {350, 280, 390, 280, 320, 230};
  int targetPulsesClose[NUM_SERVOS]= {170, 280, 390, 280, 320, 230};
  int upperPulsesClose[NUM_SERVOS] = {170, 270, 390, 180, 250, 230};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}

void c() {
  int upperPulses[NUM_SERVOS]      = {350, 450, 420, 300, 180, 220};
  int targetPulses[NUM_SERVOS]     = {350, 450, 420, 350, 230, 220};
  int targetPulsesClose[NUM_SERVOS]= {170, 450, 420, 350, 230, 220};
  int upperPulsesClose[NUM_SERVOS] = {170, 450, 420, 300, 180, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}

void scanningdrop() {
  int upperPulses[NUM_SERVOS]      = {170, 270, 390, 200, 260, 230};
  int targetPulses[NUM_SERVOS]     = {170, 290, 390, 260, 300, 230};
  int targetPulsesClose[NUM_SERVOS]= {350, 290, 390, 260, 300, 230};
  int upperPulsesClose[NUM_SERVOS] = {350, 150, 390, 200, 260, 230};
  scanning(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void scanningpick() {
  int upperPulses[NUM_SERVOS]      = {350, 270, 390, 200, 260, 230};
  int targetPulses[NUM_SERVOS]     = {350, 290, 390, 295, 320, 230};
  int targetPulsesClose[NUM_SERVOS]= {170, 290, 390, 295, 320, 230};
  int upperPulsesClose[NUM_SERVOS] = {170, 270, 390, 200, 260, 230};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b1(){
  Serial.println("Triggered b1()");
  int upperPulses[NUM_SERVOS]      = {170, 450, 420, 280, 150, 220};
  int targetPulses[NUM_SERVOS]     = {170, 450, 420, 340, 200, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 450, 420, 340, 200, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 450, 420, 280, 150, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b3(){
  Serial.println("Triggered b3()");
  int upperPulses[NUM_SERVOS]      = {170, 280, 420, 190, 215, 220};
  int targetPulses[NUM_SERVOS]     = {170, 320, 420, 250, 240, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 320, 420, 250, 240, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 280, 420, 190, 215, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b2(){
  Serial.println("Triggered b2()");
  int upperPulses[NUM_SERVOS]      = {170, 200, 420, 150, 290, 220};
  int targetPulses[NUM_SERVOS]     = {170, 220, 420, 250, 350, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 220, 420, 250, 350, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 200, 420, 150, 290, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b4(){
  Serial.println("Triggered b4()");
  int upperPulses[NUM_SERVOS]      = {170, 160, 420, 150, 360, 220};
  int targetPulses[NUM_SERVOS]     = {170, 230, 420, 360, 490, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 230, 420, 360, 490, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 160, 420, 250, 450, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void dispatchFunction(char ch) {
  switch (ch) {
    case 'a': a(); break;
    case 'b': b(); break;
    case 'c': c(); break;
    default: Serial.println("Unknown robot arm command."); break;
  }
}
void triggerSortFunction(String s) {
  if (s == "b1") sortedAreaCM1();
  else if (s == "b2") sortedAreaCM2();
  else if (s == "b3") sortedAreaCM3();
  else if (s == "b4") sortedAreaCM4();
}

// --- Stepper/Slider Functions ---
void homeStepper() {
  Serial.println("Homing slider...");
  stepper.setSpeed(-3200);
  while (digitalRead(limitHomePin) == HIGH) {
    stepper.runSpeed();
  }
  stepper.stop();
  stepper.setCurrentPosition(0);
  Serial.println("Slider homed to position 0cm.");
}
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