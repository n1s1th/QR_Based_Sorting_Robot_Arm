#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <AccelStepper.h>

// --- Robot Arm Setup ---
Adafruit_PWMServoDriver srituhobby = Adafruit_PWMServoDriver();
#define NUM_SERVOS 6
#define servoMIN 150 //0
#define servoMAX 600 // 180
int defaultPulse[NUM_SERVOS] = {200, 580, 150, 180, 220, 220};
int currentPulse[NUM_SERVOS] = {200, 580, 150, 180, 220, 220};
int stepDelay = 20;
int stepSize = 2;

// --- Stepper/Slider Setup ---
const int stepPin = 3;
const int dirPin = 2;
const int limitHomePin = 4;
const int stepsPerCM = 50;
AccelStepper stepper(AccelStepper::DRIVER, stepPin, dirPin);

// --- Movement Variables ---
int roundCount_b1 = 0;
int roundCount_b2 = 0;
int roundCount_b3 = 0;
int roundCount_b4 = 0;
const int cellWidthCM = 6;
const int scanningAreaCM = 35;

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

  stepper.setMaxSpeed(800);
  stepper.setAcceleration(400);
  homeStepper();

  Serial.println("Enter slider position (A-D) and robot arm action (a-d), separated by space, e.g.: B c");
}

// --- LOOP ---
void loop() {
  if (waitingForInitialInputs && Serial.available() > 0) {
    String inStr = Serial.readStringUntil('\n');
    inStr.trim();
    int spaceIdx = inStr.indexOf(' ');
    if (spaceIdx == -1 || spaceIdx == 0 || spaceIdx == inStr.length()-1) {
      Serial.println("Invalid input. Enter as: B c");
      Serial.println("Enter slider position (A-D) and robot arm action (a-d), separated by space:");
      return;
    }
    sliderInput = inStr.substring(0, spaceIdx);
    robotInput = inStr.substring(spaceIdx+1);

    if (!isValidSlider(sliderInput) || !isValidRobot(robotInput)) {
      Serial.println("Invalid input. Slider must be A-D and robot arm must be a-d. Try again:");
      return;
    }
    waitingForInitialInputs = false;

    // --- Workflow Update ---
    // 1. Move slider to selected position
    int cellNum = (sliderInput[0] - 'A' + 1);
    int cellCM = cellNum * cellWidthCM;
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
    Serial.println("Enter sorted area action (b1, b2, b3, b4):");
  }
  else if (waitingForSortInput && Serial.available() > 0) {
    String inStr = Serial.readStringUntil('\n');
    inStr.trim();
    if (!isValidSort(inStr)) {
      Serial.println("Invalid input. Enter b1, b2, b3, or b4:");
      return;
    }
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
    Serial.println("Enter slider position (A-D) and robot arm action (a-d), separated by space, e.g.: B c");
  }
}

// --- Input Validation ---
bool isValidSlider(String s) {
  return (s.length() == 1 && (s[0] == 'A' || s[0] == 'B' || s[0] == 'C' || s[0] == 'D'));
}
bool isValidRobot(String s) {
  return (s.length() == 1 && (s[0] == 'a' || s[0] == 'b' || s[0] == 'c' || s[0] == 'd'));
}
bool isValidSort(String s) {
  return (s == "b1" || s == "b2" || s == "b3" || s == "b4");
}

// --- Sorted Area Functions ---
void sortedAreaCM1() {
  int sortedAreaStartCM = 50;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b1 * cellWidthCM;
  Serial.print("Moving slider to sorted area for b1 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b1();
  roundCount_b1++;
}
void sortedAreaCM2() {
  int sortedAreaStartCM = 50;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b2 * cellWidthCM;
  Serial.print("Moving slider to sorted area for b2 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b2();
  roundCount_b2++;
}
void sortedAreaCM3() {
  int sortedAreaStartCM = 60;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b3 * cellWidthCM;
  Serial.print("Moving slider to sorted area for b3 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b3();
  roundCount_b3++;
}
void sortedAreaCM4() {
  int sortedAreaStartCM = 60;
  int sortedAreaCM = sortedAreaStartCM + roundCount_b4 * cellWidthCM;
  Serial.print("Moving slider to sorted area for b4 (");
  Serial.print(sortedAreaCM);
  Serial.println(" cm)");
  moveToPosition(sortedAreaCM);
  b4();
  roundCount_b4++;
}

// --- Robot Arm Functions ---
// ... (unchanged, same as your code)
// --- Use the rest of your robot arm, moving, and stepper code unchanged below this point ---
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


void a() { /* fill with your action or copy c() and edit pulses */ }
void b() { /* fill with your action or copy c() and edit pulses */ }
void c() {
  int upperPulses[NUM_SERVOS]      = {350, 490, 150, 260, 200, 220};
  int targetPulses[NUM_SERVOS]     = {350, 490, 150, 320, 250, 220};
  int targetPulsesClose[NUM_SERVOS]= {180, 490, 150, 320, 250, 220};
  int upperPulsesClose[NUM_SERVOS] = {180, 490, 150, 260, 200, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void d() { /* fill with your action or copy c() and edit pulses */ }
void scanningdrop() {
  int upperPulses[NUM_SERVOS]      = {200, 580, 150, 180, 220, 220};
  int targetPulses[NUM_SERVOS]     = {350, 580, 150, 280, 280, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 580, 150, 180, 220, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 400, 150, 170, 220, 220};
  scanning(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void scanningpick() {
  int upperPulses[NUM_SERVOS]      = {350, 400, 150, 170, 220, 220};
  int targetPulses[NUM_SERVOS]     = {350, 580, 150, 180, 220, 220};
  int targetPulsesClose[NUM_SERVOS]= {200, 580, 150, 280, 280, 220};
  int upperPulsesClose[NUM_SERVOS] = {200, 580, 150, 180, 220, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b1(){
  Serial.println("Triggered b1()");
  int upperPulses[NUM_SERVOS]      = {200, 490, 150, 260, 200, 220};
  int targetPulses[NUM_SERVOS]     = {200, 490, 150, 320, 250, 220};
  int targetPulsesClose[NUM_SERVOS]= {350, 490, 150, 320, 250, 220};
  int upperPulsesClose[NUM_SERVOS] = {350, 490, 150, 260, 200, 220};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b2(){
  Serial.println("Triggered b2()");
  int upperPulses[NUM_SERVOS]      = {210, 500, 160, 270, 210, 230};
  int targetPulses[NUM_SERVOS]     = {210, 500, 160, 330, 260, 230};
  int targetPulsesClose[NUM_SERVOS]= {360, 500, 160, 330, 260, 230};
  int upperPulsesClose[NUM_SERVOS] = {360, 500, 160, 270, 210, 230};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b3(){
  Serial.println("Triggered b3()");
  int upperPulses[NUM_SERVOS]      = {220, 510, 170, 280, 220, 240};
  int targetPulses[NUM_SERVOS]     = {220, 510, 170, 340, 270, 240};
  int targetPulsesClose[NUM_SERVOS]= {370, 510, 170, 340, 270, 240};
  int upperPulsesClose[NUM_SERVOS] = {370, 510, 170, 280, 220, 240};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void b4(){
  Serial.println("Triggered b4()");
  int upperPulses[NUM_SERVOS]      = {230, 520, 180, 290, 230, 250};
  int targetPulses[NUM_SERVOS]     = {230, 520, 180, 350, 280, 250};
  int targetPulsesClose[NUM_SERVOS]= {380, 520, 180, 350, 280, 250};
  int upperPulsesClose[NUM_SERVOS] = {380, 520, 180, 290, 230, 250};
  robotarm(upperPulses, targetPulses, targetPulsesClose, upperPulsesClose);
}
void dispatchFunction(char ch) {
  switch (ch) {
    case 'a': a(); break;
    case 'b': b(); break;
    case 'c': c(); break;
    case 'd': d(); break;
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
// ... (unchanged)
void homeStepper() {
  Serial.println("Homing slider...");
  stepper.setSpeed(-400);
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