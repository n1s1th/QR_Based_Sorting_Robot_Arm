#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver srituhobby = Adafruit_PWMServoDriver();

// Define pulse limits for safety
#define servoMIN 150
#define servoMAX 600

// Default positions
int defaultPulse[6] = {425, 450, 375, 150, 220, 220};
int currentPulse[6] = {0, 0, 0, 0, 0, 0};  // Will be updated to default at startup

// Speed tuning
int stepDelay = 10;  // ms between steps
int stepSize = 2;    // smaller = slower/smoother

String inputString = "";
bool inputReady = false;

void setup() {
  Serial.begin(9600);
  srituhobby.begin();
  srituhobby.setPWMFreq(60);  // Standard servo frequency

  Serial.println("🔄 Initializing to default positions...");

  // Move all servos to default at startup
  for (int i = 0; i < 6; i++) {
    moveServoSlow(i, defaultPulse[i]);
  }

  Serial.println("✅ Ready for calibration.");
  Serial.println("Type: servoNum pulse (e.g. 2 400) and press Enter");
  Serial.println("Valid servoNum: 0 to 5, pulse: " + String(servoMIN) + " to " + String(servoMAX));
}

void loop() {
  if (Serial.available()) {
    inputString = Serial.readStringUntil('\n');
    inputString.trim();
    inputReady = true;
  }

  if (inputReady) {
    int servoNum, pulse;
    if (parseInput(inputString, servoNum, pulse)) {
      if (servoNum >= 0 && servoNum < 6 && pulse >= servoMIN && pulse <= servoMAX) {
        moveServoSlow(servoNum, pulse);
        Serial.print("✅ Servo ");
        Serial.print(servoNum);
        Serial.print(" moved to ");
        Serial.println(pulse);
      } else {
        Serial.println("❌ Invalid servo number or pulse out of range.");
      }
    } else {
      Serial.println("⚠ Invalid input. Use: servoNum pulse (e.g. 2 400)");
    }

    inputReady = false;
  }
}

// Smooth movement function
void moveServoSlow(int servoNum, int targetPulse) {
  int current = currentPulse[servoNum];

  if (current == 0) {
    // First time moving this servo, initialize from default
    current = defaultPulse[servoNum];
  }

  if (current < targetPulse) {
    for (int p = current; p <= targetPulse; p += stepSize) {
      srituhobby.setPWM(servoNum, 0, p);
      delay(stepDelay);
    }
  } else {
    for (int p = current; p >= targetPulse; p -= stepSize) {
      srituhobby.setPWM(servoNum, 0, p);
      delay(stepDelay);
    }
  }

  currentPulse[servoNum] = targetPulse;
}

// Parse user input from Serial
bool parseInput(String input, int &servoNum, int &pulse) {
  int spaceIndex = input.indexOf(' ');
  if (spaceIndex == -1) return false;

  String part1 = input.substring(0, spaceIndex);
  String part2 = input.substring(spaceIndex + 1);

  if (part1.length() == 0 || part2.length() == 0) return false;

  servoNum = part1.toInt();
  pulse = part2.toInt();

  return true;
}