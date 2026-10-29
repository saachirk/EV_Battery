/*
  ESP32 battery monitoring prototype firmware

  IMPORTANT:
  - Do not connect an EV battery directly to an ESP32 GPIO pin.
  - Use a proper safe voltage-sensing circuit, such as a resistor divider to keep
    the ADC input within the ESP32 analog input range (0 V to 3.3 V max).
  - Use a battery current sensor such as a shunt + amplifier or a hall-effect sensor
    (for example, INA219, ACS712, or a similar suitable current sensor module).
  - Temperature and humidity sensors must use their own correct libraries and wiring.

  This file is intentionally written as a simple demonstration template. The actual
  hardware model, pins, and sensor modules must be confirmed before deployment.
*/

#include <Arduino.h>

// ---- 1) Placeholder pin configuration --------------------------------------
// Replace these values with the actual pin numbers used by your sensors.
const int BATTERY_VOLTAGE_ADC_PIN = 34;     // Example placeholder: ADC pin for battery voltage divider output
const int BATTERY_CURRENT_SENSOR_PIN = 35;  // Example placeholder: ADC pin for current sensor output
const int BATTERY_TEMP_SENSOR_PIN = 4;      // Example placeholder: DS18B20 or other temperature sensor pin
const int AMBIENT_TEMP_SENSOR_PIN = 25;     // Example placeholder: DHT22 / SHT sensor pin
const int HUMIDITY_SENSOR_PIN = 26;          // Example placeholder: DHT22 / SHT sensor pin

// Optional: use a real library if your sensor is DHT22, SHT31, etc.
// #include <DHT.h>
// DHT dht(HUMIDITY_SENSOR_PIN, DHT22);

// ---- 2) Hardware configuration ---------------------------------------------
// Safe voltage sensing notes:
// 1. Use a resistor divider or optimized analog front end to scale battery voltage to <= 3.3V.
// 2. Ensure the divider ratio is chosen for the maximum expected battery voltage.
// 3. Keep analog input wires short and filtered.
// 4. For current measurement, use a shunt, sensor module, or isolated current monitoring circuit.
// 5. Confirm all grounds are common and the ADC reference is stable.

float batteryVoltage = 0.0;
float batteryCurrent = 0.0;
float batteryTemp = 0.0;
float ambientTemp = 0.0;
float humidity = 0.0;

void setup() {
  Serial.begin(115200);
  delay(500);

  // Configure analog pins if needed.
  pinMode(BATTERY_VOLTAGE_ADC_PIN, INPUT);
  pinMode(BATTERY_CURRENT_SENSOR_PIN, INPUT);

  // Uncomment and configure if a real sensor library is installed.
  // dht.begin();

  Serial.println("ESP32 battery monitor ready.");
}

float readBatteryVoltage() {
  // Placeholder implementation. Replace with actual ADC reading and calibration.
  int raw = analogRead(BATTERY_VOLTAGE_ADC_PIN);
  float voltage = raw * (3.3 / 4095.0);  // Example only; must be calibrated for divider ratio.
  return voltage;
}

float readBatteryCurrent() {
  // Placeholder implementation. Replace with actual current sensor conversion.
  int raw = analogRead(BATTERY_CURRENT_SENSOR_PIN);
  float current = raw * (3.3 / 4095.0);  // Example only; must match sensor calibration.
  return current;
}

float readBatteryTemperature() {
  // Placeholder implementation. Replace with actual temperature sensor reading.
  return 25.0;
}

float readAmbientTemperature() {
  // Placeholder implementation. Replace with actual ambient sensor reading.
  return 24.0;
}

float readHumidity() {
  // Placeholder implementation. Replace with actual humidity sensor reading.
  return 45.0;
}

void loop() {
  batteryVoltage = readBatteryVoltage();
  batteryCurrent = readBatteryCurrent();
  batteryTemp = readBatteryTemperature();
  ambientTemp = readAmbientTemperature();
  humidity = readHumidity();

  // Message format required by the Python dashboard:
  // voltage,current,battery_temperature,ambient_temperature,humidity
  Serial.print(batteryVoltage, 2);
  Serial.print(",");
  Serial.print(batteryCurrent, 2);
  Serial.print(",");
  Serial.print(batteryTemp, 2);
  Serial.print(",");
  Serial.print(ambientTemp, 2);
  Serial.print(",");
  Serial.println(humidity, 2);

  delay(2000);
}

/*
  Example serial line:
  3.72,8.0,32.0,28.0,55.0

  This is the exact data format expected by the dashboard.
*/
