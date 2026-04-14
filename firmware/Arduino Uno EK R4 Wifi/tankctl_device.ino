// ===== CONFIG =====
#define WIFI_SSID "EMPIRE"
#define WIFI_PASSWORD "30379718"

#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883

#define REGISTRATION_SERVER "192.168.1.100"
#define REGISTRATION_PORT 8000
#define REGISTRATION_ENDPOINT "/devices/"

#define DEFAULT_TANK_ID "tank1"
#define RELAY_PIN 4 // Using pin 4 for the relay
#define ONE_WIRE_PIN 6

#define TELEMETRY_INTERVAL_MS 10000UL
#define HEARTBEAT_INTERVAL_MS 30000UL
#define WIFI_RETRY_INTERVAL_MS 5000UL
#define WIFI_CONNECT_ATTEMPT_COOLDOWN_MS 15000UL
#define HEALTH_LOG_INTERVAL_MS 60000UL
#define MQTT_RETRY_INTERVAL_MS 3000UL
#define NTP_UPDATE_INTERVAL_MS 3600000UL // Sync once every hour
#define SCHEDULE_CHECK_INTERVAL_MS 1000UL
#define TEMP_SENSOR_RESOLUTION_BITS 10
#define TEMP_CONVERSION_DELAY_MS 200UL
#define TIMEZONE_NAME "Asia/Kolkata"
#define TIMEZONE_OFFSET_SECONDS 19800

// EEPROM addresses
#define EEPROM_ADDR_TANK_ID 0
#define EEPROM_ADDR_SCHEDULE_ON_HOUR 32
#define EEPROM_ADDR_SCHEDULE_ON_MINUTE 34
#define EEPROM_ADDR_SCHEDULE_OFF_HOUR 36
#define EEPROM_ADDR_SCHEDULE_OFF_MINUTE 38
#define EEPROM_ADDR_SCHEDULE_ENABLED 40
#define EEPROM_ADDR_INIT_FLAG 41
#define EEPROM_ADDR_DEVICE_SECRET 100
#define EEPROM_ADDR_DEVICE_REGISTERED 164
#define EEPROM_INIT_FLAG 0xA5

#define TANK_ID_MAX_LEN 32
#define DEVICE_SECRET_MAX_LEN 64
#define FIRMWARE_VERSION "1.0.0"

// ===== LIBRARIES =====
#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Arduino_LED_Matrix.h>

// ===== GLOBAL STATE =====
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", TIMEZONE_OFFSET_SECONDS, 60000);

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
ArduinoLEDMatrix matrix;

uint8_t MATRIX_ON_BITMAP[8][12] = {
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0},
  {0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0},
  {0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0},
  {0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0},
  {0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
};

uint8_t MATRIX_OFF_BITMAP[8][12] = {
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0},
  {1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0},
  {1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0},
  {1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0},
  {1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
};

char tankId[TANK_ID_MAX_LEN] = {0};
char deviceSecret[DEVICE_SECRET_MAX_LEN] = {0};
bool lightState = false;
bool deviceRegistered = false;
float temperature = 0.0;
int lastCommandVersion = 0;

int scheduleOnHour = 18;
int scheduleOnMinute = 0;
int scheduleOffHour = 6;
int scheduleOffMinute = 0;
bool scheduleEnabled = false;
bool lastAppliedLightWindowState = false;  // Track last applied window state for idempotency

unsigned long lastTelemetryMs = 0;
unsigned long lastHeartbeatMs = 0;
unsigned long lastWifiRetryMs = 0;
unsigned long lastMqttRetryMs = 0;
unsigned long lastWifiBeginMs = 0;
unsigned long lastHealthLogMs = 0;
unsigned long lastNtpUpdateMs = 0;
unsigned long lastScheduleCheckMs = 0;
unsigned long tempRequestMs = 0;
bool wasWifiConnected = false;
bool wifiConnectInProgress = false;
bool tempConversionInProgress = false;
unsigned int wifiFailureCount = 0;

char topicCommand[64];
char topicReported[64];
char topicTelemetry[64];
char topicHeartbeat[64];
char topicStatus[64];

const char* wifiStatusToString(int status) {
  switch (status) {
    case WL_IDLE_STATUS:
      return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL:
      return "WL_NO_SSID_AVAIL";
    case WL_SCAN_COMPLETED:
      return "WL_SCAN_COMPLETED";
    case WL_CONNECTED:
      return "WL_CONNECTED";
    case WL_CONNECT_FAILED:
      return "WL_CONNECT_FAILED";
    case WL_CONNECTION_LOST:
      return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED:
      return "WL_DISCONNECTED";
    default:
      return "WL_UNKNOWN";
  }
}

void printWifiScanResults() {
  Serial.println("Scanning nearby WiFi networks...");
  int networkCount = WiFi.scanNetworks();

  if (networkCount <= 0) {
    Serial.println("No WiFi networks found");
    return;
  }

  bool targetFound = false;
  for (int i = 0; i < networkCount; i++) {
    int rssi = WiFi.RSSI(i);
    int encryption = WiFi.encryptionType(i);

    Serial.print("  ");
    Serial.print(i + 1);
    Serial.print(": SSID hidden");
    Serial.print(" RSSI=");
    Serial.print(rssi);
    Serial.print("dBm ENC=");
    Serial.println(encryption);

    // Avoid String-heavy SSID retrieval in diagnostics path to reduce heap churn.
    targetFound = true;
  }

  if (!targetFound) {
    Serial.print("Target SSID not visible: ");
    Serial.println(WIFI_SSID);
  }
}

void showLightStateOnMatrix(bool state) {
  if (state) {
    matrix.renderBitmap(MATRIX_ON_BITMAP, 8, 12);
  } else {
    matrix.renderBitmap(MATRIX_OFF_BITMAP, 8, 12);
  }
}

// ===== SETUP =====
void setup() {
  Serial.begin(9600);
  delay(1000);
  
  Serial.println("TankCtl Device Starting...");
  
  // Initialize relay pin
  // Set as output first, then explicitly drive it
  pinMode(RELAY_PIN, OUTPUT);
  // Default to OFF (For Active-LOW relays, this is HIGH)
  digitalWrite(RELAY_PIN, HIGH);

  // Initialize LED matrix and show current light state
  matrix.begin();
  showLightStateOnMatrix(lightState);
  
  // Load configuration from EEPROM
  loadConfig();
  
  // Build MQTT topics
  buildTopics();
  
  // Initialize temperature sensor
  sensors.begin();
  // 10-bit resolution shortens conversion time and reduces loop blocking.
  sensors.setResolution(TEMP_SENSOR_RESOLUTION_BITS);
  sensors.setWaitForConversion(false);
  sensors.requestTemperatures();
  tempRequestMs = millis();
  tempConversionInProgress = true;
  
  // Connect WiFi
  Serial.print("WiFi firmware: ");
  Serial.println(WiFi.firmwareVersion());
  connectWiFi();
  
  // Try device registration if needed (after WiFi connects)
  if (WiFi.status() == WL_CONNECTED) {
    if (!deviceRegistered) {
      registerDevice();
    }
    
    // Always try to sync schedule from API (even if registration failed)
    // This ensures we get the latest schedule even during partial outages
    syncScheduleFromAPI();
  }
  
  // Synchronize time
  Serial.print("Timezone: ");
  Serial.print(TIMEZONE_NAME);
  Serial.print(" (UTC+");
  Serial.print(TIMEZONE_OFFSET_SECONDS / 3600);
  Serial.println(":30)");
  timeClient.begin();
  Serial.println("Synchronizing time with NTP...");
  timeClient.update();
  
  // Apply initial scheduled light state after NTP sync completes
  // This handles boot-time recovery: if device boots within a scheduled lighting window,
  // lights will be turned ON immediately rather than waiting for the exact minute match.
  Serial.println("\n[Boot] Applying initial scheduled light state after NTP sync...");
  Serial.print("[Boot] scheduleEnabled=");
  Serial.print(scheduleEnabled ? "true" : "false");
  Serial.print(" on=");
  Serial.print(scheduleOnHour);
  Serial.print(":");
  Serial.print(scheduleOnMinute);
  Serial.print(" off=");
  Serial.print(scheduleOffHour);
  Serial.print(":");
  Serial.println(scheduleOffMinute);
  Serial.print("[Boot] Current time: ");
  Serial.print(timeClient.getHours());
  Serial.print(":");
  Serial.println(timeClient.getMinutes());
  
  // Force re-evaluation by resetting the idempotency tracker
  lastAppliedLightWindowState = !isCurrentTimeInLightingWindow();  // Invert to force first application
  applyScheduledLightState();
  
  // Connect MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  if (WiFi.status() == WL_CONNECTED) {
    connectMQTT();
  } else {
    Serial.println("Skipping MQTT connect: WiFi not connected");
  }
  
  Serial.println("TankCtl Device Ready");
}

// ===== MAIN LOOP =====
void loop() {
  unsigned long now = millis();
  int wifiStatus = WiFi.status();
  bool wifiConnected = wifiStatus == WL_CONNECTED;

  if (wifiConnected) {
    wifiConnectInProgress = false;
  }

  if (wifiConnected != wasWifiConnected) {
    if (wifiConnected) {
      Serial.print("WiFi connected. IP: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.print("WiFi disconnected. WiFi.status()=");
      Serial.print(wifiStatus);
      Serial.print(" (");
      Serial.print(wifiStatusToString(wifiStatus));
      Serial.println(")");
    }
    wasWifiConnected = wifiConnected;
  }
  
  // Ensure WiFi connection
  if (!wifiConnected) {
    if (now - lastWifiRetryMs >= WIFI_RETRY_INTERVAL_MS) {
      lastWifiRetryMs = now;
      connectWiFi();
    }
  }
  
  // Ensure MQTT connection only when WiFi is available
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      if (now - lastMqttRetryMs >= MQTT_RETRY_INTERVAL_MS) {
        lastMqttRetryMs = now;
        connectMQTT();
      }
    } else {
      mqttClient.loop();
    }
  } else if (mqttClient.connected()) {
    mqttClient.disconnect();
    Serial.println("MQTT disconnected: WiFi lost");
  }
  
  // Update NTP at a controlled interval instead of every loop iteration.
  if (now - lastNtpUpdateMs >= NTP_UPDATE_INTERVAL_MS) {
    lastNtpUpdateMs = now;
    timeClient.update();
  }
  
  // Run local scheduler
  if (now - lastScheduleCheckMs >= SCHEDULE_CHECK_INTERVAL_MS) {
    lastScheduleCheckMs = now;
    runSchedule();
  }
  
  // Publish telemetry
  if (now - lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryMs = now;
    publishTelemetry();
  }
  
  // Publish heartbeat
  if (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatMs = now;
    publishHeartbeat();
  }

  // Periodic health log to correlate connectivity with unexpected resets.
  if (now - lastHealthLogMs >= HEALTH_LOG_INTERVAL_MS) {
    lastHealthLogMs = now;
    Serial.print("Health: uptime_ms=");
    Serial.print(now);
    Serial.print(" wifi=");
    Serial.print(wifiStatusToString(WiFi.status()));
    Serial.print(" mqtt=");
    Serial.println(mqttClient.connected() ? "connected" : "disconnected");
  }

  // Short yield keeps network stack responsive on long runtimes.
  delay(1);
}

// ===== WIFI FUNCTIONS =====
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  unsigned long now = millis();
  if (wifiConnectInProgress && (now - lastWifiBeginMs) < WIFI_CONNECT_ATTEMPT_COOLDOWN_MS) {
    return;
  }
  
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  // Avoid disconnecting on every retry; repeated disconnect/begin loops can destabilize WiFiS3.
  int beginStatus = WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWifiBeginMs = now;
  wifiConnectInProgress = true;
  Serial.print("WiFi.begin() status=");
  Serial.print(beginStatus);
  Serial.print(" (");
  Serial.print(wifiStatusToString(beginStatus));
  Serial.println(")");

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
    wasWifiConnected = true;
    wifiConnectInProgress = false;
    wifiFailureCount = 0;
  } else {
    wifiFailureCount++;
    Serial.println("WiFi connect pending/failed; will retry after cooldown");
    Serial.print("WiFi.status()=");
    Serial.print(WiFi.status());
    Serial.print(" (");
    Serial.print(wifiStatusToString(WiFi.status()));
    Serial.println(")");

    // WiFi scanning is expensive; do it less frequently during long outages.
    if (wifiFailureCount % 10 == 0) {
      printWifiScanResults();
    }
  }
}

// ===== MQTT FUNCTIONS =====
void connectMQTT() {
  if (mqttClient.connected()) {
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Skipping MQTT connect: WiFi not connected");
    return;
  }
  
  char clientId[48];
  snprintf(clientId, sizeof(clientId), "tankctl-%s", tankId);
  
  Serial.print("Connecting to MQTT broker: ");
  Serial.println(MQTT_SERVER);
  
  if (mqttClient.connect(clientId)) {
    Serial.println("MQTT connected");
    
    // Subscribe to command topic
    mqttClient.subscribe(topicCommand);
    Serial.print("Subscribed to: ");
    Serial.println(topicCommand);
    
    // Publish initial heartbeat and reported state
    publishHeartbeat();
    publishReportedState();
  } else {
    Serial.print("MQTT connection failed, rc=");
    Serial.println(mqttClient.state());
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on: ");
  Serial.println(topic);
  
  // Parse JSON
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  handleCommand(doc);
}

void buildTopics() {
  snprintf(topicCommand, sizeof(topicCommand), "tankctl/%s/command", tankId);
  snprintf(topicReported, sizeof(topicReported), "tankctl/%s/reported", tankId);
  snprintf(topicTelemetry, sizeof(topicTelemetry), "tankctl/%s/telemetry", tankId);
  snprintf(topicHeartbeat, sizeof(topicHeartbeat), "tankctl/%s/heartbeat", tankId);
  snprintf(topicStatus,    sizeof(topicStatus),    "tankctl/%s/status",    tankId);
}

// ===== COMMAND HANDLER =====
void handleCommand(JsonDocument& doc) {
  if (!doc.containsKey("version") || !doc.containsKey("command")) {
    Serial.println("Invalid command: missing version or command");
    return;
  }
  
  int version = doc["version"];
  const char* command = doc["command"];
  
  // Check version to prevent duplicate execution
  if (version <= lastCommandVersion) {
    Serial.print("Ignoring old command version: ");
    Serial.println(version);
    return;
  }
  
  lastCommandVersion = version;
  Serial.print("Executing command: ");
  Serial.print(command);
  Serial.print(" (version ");
  Serial.print(version);
  Serial.println(")");
  
  if (strcmp(command, "set_light") == 0) {
    handleSetLight(doc);
  } else if (strcmp(command, "set_schedule") == 0) {
    handleSetSchedule(doc);
  } else if (strcmp(command, "reboot_device") == 0) {
    handleRebootDevice();
  } else {
    Serial.print("Unknown command: ");
    Serial.println(command);
  }
}

void handleSetLight(JsonDocument& doc) {
  if (!doc.containsKey("value")) {
    Serial.println("set_light: missing value");
    return;
  }
  
  const char* value = doc["value"];
  bool newState = (strcmp(value, "on") == 0);
  
  setLight(newState);
  publishReportedState();
}

void handleSetSchedule(JsonDocument& doc) {
  if (!doc.containsKey("on_time") || !doc.containsKey("off_time")) {
    Serial.println("set_schedule: missing on_time or off_time");
    return;
  }
  
  const char* onTime = doc["on_time"];
  const char* offTime = doc["off_time"];
  
  // Parse on_time (format: "HH:MM")
  int onHour, onMinute;
  if (sscanf(onTime, "%d:%d", &onHour, &onMinute) != 2) {
    Serial.println("set_schedule: invalid on_time format");
    return;
  }
  
  // Parse off_time
  int offHour, offMinute;
  if (sscanf(offTime, "%d:%d", &offHour, &offMinute) != 2) {
    Serial.println("set_schedule: invalid off_time format");
    return;
  }
  
  // Update schedule
  scheduleOnHour = onHour;
  scheduleOnMinute = onMinute;
  scheduleOffHour = offHour;
  scheduleOffMinute = offMinute;
  scheduleEnabled = true;
  
  // Reset window state tracker so applyScheduledLightState() will re-evaluate
  lastAppliedLightWindowState = false;
  
  // Save to EEPROM
  saveSchedule();

  Serial.print("Schedule updated: ON ");
  Serial.print(onTime);
  Serial.print(", OFF ");
  Serial.println(offTime);
  
  // Apply new schedule immediately
  Serial.println("Applying new schedule...");
  applyScheduledLightState();
  
  publishReportedState();
}

void handleRebootDevice() {
  Serial.println("Reboot command received");

  // Publish final state before reset so backend has a fresh reported snapshot.
  publishReportedState();
  publishHeartbeat();

  // Give MQTT a brief window to flush outbound packets.
  unsigned long flushStart = millis();
  while (millis() - flushStart < 300) {
    mqttClient.loop();
    delay(10);
  }

  Serial.println("Rebooting now...");
  Serial.flush();
  delay(100);

  // UNO R4 WiFi is Cortex-M based; use core reset.
  NVIC_SystemReset();
}

// ===== LIGHT CONTROL =====
void setLight(bool state) {
  lightState = state;
  // Make sure we print the state being written so we can debug it
  int pinState = state ? LOW : HIGH;
  Serial.print("Writing pin state: ");
  Serial.println(pinState == HIGH ? "HIGH" : "LOW");
  
  digitalWrite(RELAY_PIN, pinState);
  showLightStateOnMatrix(state);
  
  Serial.print("Light logic state: ");
  Serial.println(state ? "ON" : "OFF");
}

// ===== TELEMETRY =====
void publishTelemetry() {
  if (!mqttClient.connected()) {
    return;
  }

  if (!tempConversionInProgress) {
    sensors.requestTemperatures();
    tempRequestMs = millis();
    tempConversionInProgress = true;
    return;
  }

  unsigned long now = millis();
  if (now - tempRequestMs < TEMP_CONVERSION_DELAY_MS) {
    return;
  }
  
  // Read completed asynchronous conversion.
  float tempReading = sensors.getTempCByIndex(0);
  sensors.requestTemperatures();
  tempRequestMs = now;
  tempConversionInProgress = true;

  // Build JSON — send 0 when sensor is disconnected/invalid so the backend
  // still receives a telemetry event and can signal "unavailable" to clients.
  StaticJsonDocument<128> doc;

  bool sensorValid = !(tempReading == DEVICE_DISCONNECTED_C ||
                       tempReading < -55.0 || tempReading > 125.0);
  if (sensorValid) {
    temperature = tempReading;
    Serial.print("Telemetry: temp=");
    Serial.print(temperature);
    Serial.println("°C");
  } else {
    temperature = 0;
    Serial.println("Telemetry: sensor unavailable, sending temperature=0");

    // Publish a warning so the backend and app know the sensor may be missing.
    StaticJsonDocument<128> warnDoc;
    warnDoc["event"]   = "warning";
    warnDoc["code"]    = "sensor_unavailable";
    warnDoc["message"] = "Temperature sensor not connected or reading invalid";
    char warnBuf[128];
    serializeJson(warnDoc, warnBuf);
    mqttClient.publish(topicStatus, warnBuf);
  }

  doc["temperature"] = temperature;

  char buffer[128];
  serializeJson(doc, buffer);

  mqttClient.publish(topicTelemetry, buffer);
}

void publishHeartbeat() {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<128> doc;
  doc["status"] = "online";
  doc["uptime_ms"] = millis();
  doc["rssi"] = WiFi.RSSI();
  doc["wifi"] = wifiStatusToString(WiFi.status());
  doc["firmware_version"] = FIRMWARE_VERSION;
  
  char buffer[128];
  serializeJson(doc, buffer);
  
  mqttClient.publish(topicHeartbeat, buffer);
  
  Serial.println("Heartbeat sent");
}

void publishReportedState() {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<128> doc;
  doc["light"] = lightState ? "on" : "off";
  
  char buffer[128];
  serializeJson(doc, buffer);
  
  mqttClient.publish(topicReported, buffer);
  
  Serial.print("Reported state: light=");
  Serial.println(lightState ? "on" : "off");
}

// ===== LIGHTING WINDOW LOGIC =====
bool isCurrentTimeInLightingWindow() {
  if (!scheduleEnabled) {
    return false;
  }
  
  int currentHour = timeClient.getHours();
  int currentMinute = timeClient.getMinutes();
  
  // Convert to minutes since midnight for easier range checking
  int currentTime = currentHour * 60 + currentMinute;
  int onTime = scheduleOnHour * 60 + scheduleOnMinute;
  int offTime = scheduleOffHour * 60 + scheduleOffMinute;
  
  // Case 1: Normal schedule (on-time before off-time, e.g., 18:00 to 06:00 wrapped)
  // Check if current time is >= on-time AND <= off-time
  if (onTime <= offTime) {
    return currentTime >= onTime && currentTime <= offTime;
  }
  // Case 2: Wrap-around schedule (e.g., 18:00 to 06:00 next day)
  // Light is ON from on-time to 23:59 OR from 00:00 to off-time
  else {
    return currentTime >= onTime || currentTime <= offTime;
  }
}

// Apply scheduled light state, respecting idempotency
void applyScheduledLightState() {
  bool shouldBeLit = isCurrentTimeInLightingWindow();
  
  // Only log and change state if the window status has changed
  if (shouldBeLit != lastAppliedLightWindowState) {
    lastAppliedLightWindowState = shouldBeLit;
    
    if (shouldBeLit) {
      Serial.println("[Schedule] APPLY: Lights should be ON (within window)");
      if (!lightState) {
        Serial.println("[Schedule] Turning relay ON");
        setLight(true);
        publishReportedState();
      } else {
        Serial.println("[Schedule] Lights already ON, no change");
      }
    } else {
      Serial.println("[Schedule] APPLY: Lights should be OFF (outside window)");
      if (lightState) {
        Serial.println("[Schedule] Turning relay OFF");
        setLight(false);
        publishReportedState();
      } else {
        Serial.println("[Schedule] Lights already OFF, no change");
      }
    }
  }
  // No logging when state hasn't changed - this eliminates spam
}

// ===== SCHEDULER =====
void runSchedule() {
  applyScheduledLightState();
}

// ===== EEPROM FUNCTIONS =====
void loadConfig() {
  // Check if EEPROM is initialized
  byte initFlag = EEPROM.read(EEPROM_ADDR_INIT_FLAG);
  
  if (initFlag == EEPROM_INIT_FLAG) {
    // Load tank ID
    for (int i = 0; i < TANK_ID_MAX_LEN; i++) {
      tankId[i] = EEPROM.read(EEPROM_ADDR_TANK_ID + i);
      if (tankId[i] == 0) break;
    }
    tankId[TANK_ID_MAX_LEN - 1] = 0;
    
    // Load device secret (if exists, device is registered)
    byte registered = EEPROM.read(EEPROM_ADDR_DEVICE_REGISTERED);
    if (registered == 1) {
      for (int i = 0; i < DEVICE_SECRET_MAX_LEN; i++) {
        deviceSecret[i] = EEPROM.read(EEPROM_ADDR_DEVICE_SECRET + i);
        if (deviceSecret[i] == 0) break;
      }
      deviceSecret[DEVICE_SECRET_MAX_LEN - 1] = 0;
      deviceRegistered = true;
      Serial.println("Device already registered (secret found in EEPROM)");
    } else {
      deviceRegistered = false;
      Serial.println("Device not registered yet (no secret in EEPROM)");
    }
    
    // Load schedule
    scheduleOnHour = EEPROM.read(EEPROM_ADDR_SCHEDULE_ON_HOUR);
    scheduleOnMinute = EEPROM.read(EEPROM_ADDR_SCHEDULE_ON_MINUTE);
    scheduleOffHour = EEPROM.read(EEPROM_ADDR_SCHEDULE_OFF_HOUR);
    scheduleOffMinute = EEPROM.read(EEPROM_ADDR_SCHEDULE_OFF_MINUTE);
    scheduleEnabled = EEPROM.read(EEPROM_ADDR_SCHEDULE_ENABLED);
    
    Serial.print("Loaded config from EEPROM. Tank ID: ");
    Serial.println(tankId);
  } else {
    // First boot - initialize with defaults
    Serial.println("First boot - initializing EEPROM with defaults");
    strncpy(tankId, DEFAULT_TANK_ID, TANK_ID_MAX_LEN - 1);
    tankId[TANK_ID_MAX_LEN - 1] = 0;
    
    deviceRegistered = false;
    
    saveTankId();
    saveSchedule();
    EEPROM.write(EEPROM_ADDR_INIT_FLAG, EEPROM_INIT_FLAG);
    EEPROM.write(EEPROM_ADDR_DEVICE_REGISTERED, 0);
  }
}

void saveTankId() {
  for (int i = 0; i < TANK_ID_MAX_LEN; i++) {
    EEPROM.write(EEPROM_ADDR_TANK_ID + i, tankId[i]);
    if (tankId[i] == 0) break;
  }
  
  Serial.println("Tank ID saved to EEPROM");
}

void saveSchedule() {
  EEPROM.write(EEPROM_ADDR_SCHEDULE_ON_HOUR, scheduleOnHour);
  EEPROM.write(EEPROM_ADDR_SCHEDULE_ON_MINUTE, scheduleOnMinute);
  EEPROM.write(EEPROM_ADDR_SCHEDULE_OFF_HOUR, scheduleOffHour);
  EEPROM.write(EEPROM_ADDR_SCHEDULE_OFF_MINUTE, scheduleOffMinute);
  EEPROM.write(EEPROM_ADDR_SCHEDULE_ENABLED, scheduleEnabled);
  
  Serial.println("Schedule saved to EEPROM");
}

void saveDeviceSecret() {
  // Save device secret
  for (int i = 0; i < DEVICE_SECRET_MAX_LEN; i++) {
    EEPROM.write(EEPROM_ADDR_DEVICE_SECRET + i, deviceSecret[i]);
    if (deviceSecret[i] == 0) break;
  }
  
  // Mark device as registered
  EEPROM.write(EEPROM_ADDR_DEVICE_REGISTERED, 1);
  
  Serial.println("Device secret saved to EEPROM");
}

// ===== DEVICE REGISTRATION =====
void registerDevice() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Registration] WiFi not connected, skipping registration");
    return;
  }
  
  if (deviceRegistered && strlen(deviceSecret) > 0) {
    Serial.println("[Registration] Device already registered with secret");
    return;
  }
  
  Serial.println("\n[Registration] Starting device registration...");
  Serial.print("[Registration] Tank ID: ");
  Serial.println(tankId);
  
  // Create HTTP request
  WiFiClient httpClient;
  
  if (!httpClient.connect(REGISTRATION_SERVER, REGISTRATION_PORT)) {
    Serial.print("[Registration] Failed to connect to ");
    Serial.print(REGISTRATION_SERVER);
    Serial.print(":");
    Serial.println(REGISTRATION_PORT);
    return;
  }
  
  Serial.print("[Registration] Connected to ");
  Serial.print(REGISTRATION_SERVER);
  Serial.print(":");
  Serial.println(REGISTRATION_PORT);
  
  // Build JSON payload using bounded buffer
  static char payload[256];
  StaticJsonDocument<128> requestDoc;
  requestDoc["device_id"] = tankId;
  serializeJson(requestDoc, payload, sizeof(payload));
  
  // Build HTTP request using snprintf (no String class!)
  static char request[512];
  int payloadLen = strlen(payload);
  snprintf(request, sizeof(request),
    "POST %s HTTP/1.1\r\n"
    "Host: %s:%d\r\n"
    "Content-Type: application/json\r\n"
    "Content-Length: %d\r\n"
    "Connection: close\r\n"
    "\r\n"
    "%s",
    REGISTRATION_ENDPOINT,
    REGISTRATION_SERVER,
    REGISTRATION_PORT,
    payloadLen,
    payload);
  
  Serial.print("[Registration] Sending request... ");
  httpClient.print(request);
  Serial.println("done");
  
  // Wait for response (bounded buffer, no String fragmentation)
  unsigned long timeout = millis() + 5000;  // 5 second timeout
  static char response[2048];
  int responseLen = 0;
  
  while (httpClient.connected() || httpClient.available()) {
    if (millis() > timeout) {
      Serial.println("[Registration] Response timeout");
      break;
    }
    
    if (httpClient.available() && responseLen < (int)(sizeof(response) - 1)) {
      char c = httpClient.read();
      response[responseLen++] = c;
    }
    delay(1);
  }
  response[responseLen] = '\0';
  
  httpClient.stop();
  
  // Extract HTTP status code from response
  int statusCode = 200;
  const char* statusCodeStr = strstr(response, "HTTP/1.1");
  if (statusCodeStr != nullptr) {
    sscanf(statusCodeStr, "HTTP/1.1 %d", &statusCode);
  }
  
  Serial.print("[Registration] HTTP Status: ");
  Serial.println(statusCode);
  
  // Parse response
  if (responseLen > 0) {
    // Find JSON part (skip HTTP headers)
    const char* jsonStart = strstr(response, "\r\n\r\n");
    if (jsonStart != nullptr) {
      jsonStart += 4;  // Skip "\r\n\r\n"
      
      Serial.print("[Registration] Raw response: ");
      Serial.println(jsonStart);
      
      StaticJsonDocument<512> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, jsonStart);
      
      if (!error) {
        if (statusCode == 409) {
          // Device already registered - mark as registered without secret
          Serial.println("[Registration] ✓ Device already registered on backend (409 Conflict)");
          deviceRegistered = true;
        } else if (responseDoc.containsKey("device_secret")) {
          const char* secret = responseDoc["device_secret"];
          strncpy(deviceSecret, secret, DEVICE_SECRET_MAX_LEN - 1);
          deviceSecret[DEVICE_SECRET_MAX_LEN - 1] = 0;
          
          // Save to EEPROM
          saveDeviceSecret();
          deviceRegistered = true;
          
          Serial.println("[Registration] ✓ Device registered successfully!");
          Serial.print("[Registration] Device Secret (first 16 chars): ");
          for (int i = 0; i < 16 && secret[i] != '\0'; i++) {
            Serial.print(secret[i]);
          }
          Serial.println("...");
        } else {
          Serial.println("[Registration] ✗ Unexpected response (no device_secret)");
          Serial.print("[Registration] Keys in response: ");
          for (JsonPair p : responseDoc.as<JsonObject>()) {
            Serial.print(p.key().c_str());
            Serial.print(" ");
          }
          Serial.println();
        }
      } else {
        Serial.print("[Registration] ✗ JSON parse error: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.println("[Registration] ✗ No JSON found in response");
    }
  } else {
    Serial.println("[Registration] ✗ Empty response from server");
  }
  
  Serial.println();
}

// ===== SCHEDULE SYNC FROM API =====
void syncScheduleFromAPI() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Schedule Sync] WiFi not connected, skipping");
    return;
  }
  
  Serial.println("\n[Schedule Sync] Starting schedule sync from API...");
  Serial.print("[Schedule Sync] Tank ID: ");
  Serial.println(tankId);
  
  // Create HTTP request
  WiFiClient httpClient;
  
  if (!httpClient.connect(REGISTRATION_SERVER, REGISTRATION_PORT)) {
    Serial.print("[Schedule Sync] Failed to connect to ");
    Serial.print(REGISTRATION_SERVER);
    Serial.print(":");
    Serial.println(REGISTRATION_PORT);
    return;
  }
  
  Serial.print("[Schedule Sync] Connected to ");
  Serial.print(REGISTRATION_SERVER);
  Serial.print(":");
  Serial.println(REGISTRATION_PORT);
  
  // Build HTTP GET request for schedule endpoint
  static char request[256];
  snprintf(request, sizeof(request),
    "GET /devices/%s/schedule HTTP/1.1\r\n"
    "Host: %s:%d\r\n"
    "Connection: close\r\n"
    "\r\n",
    tankId,
    REGISTRATION_SERVER,
    REGISTRATION_PORT);
  
  Serial.print("[Schedule Sync] Sending request... ");
  httpClient.print(request);
  Serial.println("done");
  
  // Wait for response (bounded buffer)
  unsigned long timeout = millis() + 5000;  // 5 second timeout
  static char response[2048];
  int responseLen = 0;
  
  while (httpClient.connected() || httpClient.available()) {
    if (millis() > timeout) {
      Serial.println("[Schedule Sync] Response timeout");
      break;
    }
    
    if (httpClient.available() && responseLen < (int)(sizeof(response) - 1)) {
      char c = httpClient.read();
      response[responseLen++] = c;
    }
    delay(1);
  }
  response[responseLen] = '\0';
  
  httpClient.stop();
  
  // Extract HTTP status code
  int statusCode = 200;
  const char* statusCodeStr = strstr(response, "HTTP/1.1");
  if (statusCodeStr != nullptr) {
    sscanf(statusCodeStr, "HTTP/1.1 %d", &statusCode);
  }
  
  Serial.print("[Schedule Sync] HTTP Status: ");
  Serial.println(statusCode);
  
  // Parse response
  if (responseLen > 0) {
    // Find JSON part (skip HTTP headers)
    const char* jsonStart = strstr(response, "\r\n\r\n");
    if (jsonStart != nullptr) {
      jsonStart += 4;  // Skip "\r\n\r\n"
      
      Serial.print("[Schedule Sync] Raw response: ");
      Serial.println(jsonStart);
      
      StaticJsonDocument<256> scheduleDoc;
      DeserializationError error = deserializeJson(scheduleDoc, jsonStart);
      
      if (!error && statusCode == 200) {
        if (scheduleDoc.containsKey("on_time") && 
            scheduleDoc.containsKey("off_time") && 
            scheduleDoc.containsKey("enabled")) {
          
          const char* onTimeStr = scheduleDoc["on_time"];
          const char* offTimeStr = scheduleDoc["off_time"];
          bool enabled = scheduleDoc["enabled"];
          
          // Parse on_time (format: "HH:MM")
          int newOnHour, newOnMinute;
          if (sscanf(onTimeStr, "%d:%d", &newOnHour, &newOnMinute) != 2) {
            Serial.println("[Schedule Sync] ✗ Invalid on_time format");
            return;
          }
          
          // Parse off_time
          int newOffHour, newOffMinute;
          if (sscanf(offTimeStr, "%d:%d", &newOffHour, &newOffMinute) != 2) {
            Serial.println("[Schedule Sync] ✗ Invalid off_time format");
            return;
          }
          
          // Update schedule
          scheduleOnHour = newOnHour;
          scheduleOnMinute = newOnMinute;
          scheduleOffHour = newOffHour;
          scheduleOffMinute = newOffMinute;
          scheduleEnabled = enabled;
          
          // Reset state tracker for re-evaluation
          lastAppliedLightWindowState = false;
          
          // Save to EEPROM
          saveSchedule();
          
          Serial.print("[Schedule Sync] ✓ Schedule synced: ON ");
          Serial.print(newOnHour);
          Serial.print(":");
          Serial.print(newOnMinute);
          Serial.print(", OFF ");
          Serial.print(newOffHour);
          Serial.print(":");
          Serial.print(newOffMinute);
          Serial.print(" (enabled=");
          Serial.print(enabled ? "true" : "false");
          Serial.println(")");
        } else {
          Serial.println("[Schedule Sync] ✗ Response missing schedule fields");
        }
      } else {
        Serial.print("[Schedule Sync] ✗ JSON parse error or 404: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.println("[Schedule Sync] ✗ No JSON found in response");
    }
  } else {
    Serial.println("[Schedule Sync] ✗ Empty response from server");
  }
  
  Serial.println();
}
