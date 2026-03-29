// ===== CONFIG =====
#define WIFI_SSID "EMPIRE"
#define WIFI_PASSWORD "30379718"

#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883

#define REGISTRATION_SERVER "192.168.1.100"
#define REGISTRATION_PORT 8000
#define REGISTRATION_ENDPOINT "/devices"

#define DEFAULT_TANK_ID "POND-ESP32"
#define RELAY_PIN 4        // GPIO 4 for relay
#define ONE_WIRE_PIN 23    // GPIO 23 for temperature sensor
#define STATUS_LED_PIN 2   // GPIO 2 for status LED (optional, built-in on many ESP32 boards)

#define TELEMETRY_INTERVAL_MS 10000UL
#define HEARTBEAT_INTERVAL_MS 30000UL
#define WIFI_RETRY_INTERVAL_MS 5000UL
#define HEALTH_LOG_INTERVAL_MS 60000UL
#define MQTT_RETRY_INTERVAL_MS 3000UL
#define NTP_UPDATE_INTERVAL_MS 3600000UL // Sync once every hour
#define SCHEDULE_CHECK_INTERVAL_MS 1000UL
#define TEMP_SENSOR_RESOLUTION_BITS 10
#define TEMP_CONVERSION_DELAY_MS 200UL
#define TIMEZONE_NAME "Asia/Kolkata"
#define TIMEZONE_OFFSET_SECONDS 19800

#define TANK_ID_MAX_LEN 32
#define DEVICE_SECRET_MAX_LEN 64
#define FIRMWARE_VERSION "1.0.0-esp32"

// ===== LIBRARIES =====
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Preferences.h>
#include <time.h>

// Random temp range for testing (disable sensor reading)
#define USE_RANDOM_TEMP 1  // Set to 0 to use real DS18B20 sensor
#define TEMP_MIN 22.0f
#define TEMP_MAX 32.0f

// ===== GLOBAL STATE =====
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
Preferences preferences;
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);

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

unsigned long lastTelemetryMs = 0;
unsigned long lastHeartbeatMs = 0;
unsigned long lastWifiRetryMs = 0;
unsigned long lastMqttRetryMs = 0;
unsigned long lastHealthLogMs = 0;
unsigned long lastNtpUpdateMs = 0;
unsigned long lastScheduleCheckMs = 0;
unsigned long tempRequestMs = 0;
bool wasWifiConnected = false;
bool tempConversionInProgress = false;

char topicCommand[64];
char topicReported[64];
char topicTelemetry[64];
char topicHeartbeat[64];
char topicStatus[64];

void updateStatusLED(bool wifiConnected, bool mqttConnected) {
  if (wifiConnected && mqttConnected) {
    digitalWrite(STATUS_LED_PIN, HIGH);  // Solid (both connected)
  } else if (wifiConnected) {
    digitalWrite(STATUS_LED_PIN, HIGH);  // Could implement pulse pattern here
  } else {
    digitalWrite(STATUS_LED_PIN, LOW);   // Off (no WiFi)
  }
}

// ===== SETUP =====
void setup() {
  Serial.begin(9600);
  delay(1000);
  
  Serial.println("\n\n=== TankCtl ESP32 Device Starting ===\n");
  
  // Seed random number generator
  randomSeed(analogRead(0));
  
  // Setup pins
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);  // Relay OFF (active-low)
  
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);  // Initially off
  
  // Initialize Preferences (NVS - Non-Volatile Storage)
  preferences.begin("tankctl", false);
  
  // Load configuration
  loadConfig();
  
  // Build MQTT topics
  buildTopics();
  
  // Initialize temperature sensor (or random mode)
#if USE_RANDOM_TEMP
  Serial.println("Using RANDOM temperature mode (22-32°C) for testing");
#else
  sensors.begin();
  sensors.setResolution(TEMP_SENSOR_RESOLUTION_BITS);
  sensors.setWaitForConversion(false);
  sensors.requestTemperatures();
  tempRequestMs = millis();
  tempConversionInProgress = true;
  Serial.println("Using DS18B20 temperature sensor");
#endif
  
  // Configure WiFi
  WiFi.mode(WIFI_STA);
  connectWiFi();
  
  // Try device registration if needed (after WiFi connects)
  if (WiFi.status() == WL_CONNECTED) {
    if (!deviceRegistered) {
      registerDevice();
    }
  }
  
  // Configure time via NTP
  configTime(TIMEZONE_OFFSET_SECONDS, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Timezone: ");
  Serial.print(TIMEZONE_NAME);
  Serial.print(" (UTC+");
  Serial.print(TIMEZONE_OFFSET_SECONDS / 3600);
  Serial.println(":30)");
  Serial.println("Synchronizing time with NTP...");
  
  // Wait for time to be set (with timeout)
  time_t now = time(nullptr);
  int attempts = 0;
  while (now < 24 * 3600 && attempts < 20) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    attempts++;
  }
  Serial.println();
  
  // Connect MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  if (WiFi.status() == WL_CONNECTED) {
    connectMQTT();
  }
  
  Serial.println("TankCtl ESP32 Device Ready\n");
}

// ===== MAIN LOOP =====
void loop() {
  unsigned long now = millis();
  bool wifiConnected = WiFi.status() == WL_CONNECTED;
  bool mqttConnected = mqttClient.connected();
  
  // Handle WiFi status changes
  if (wifiConnected != wasWifiConnected) {
    if (wifiConnected) {
      Serial.print("WiFi connected. IP: ");
      Serial.println(WiFi.localIP());
      lastMqttRetryMs = 0;  // Reset MQTT retry timer
    } else {
      Serial.println("WiFi disconnected");
      if (mqttConnected) {
        mqttClient.disconnect();
      }
    }
    wasWifiConnected = wifiConnected;
  }
  
  // Update LED status
  updateStatusLED(wifiConnected, mqttConnected);
  
  // WiFi reconnection
  if (!wifiConnected) {
    if (now - lastWifiRetryMs >= WIFI_RETRY_INTERVAL_MS) {
      lastWifiRetryMs = now;
      connectWiFi();
    }
  }
  
  // MQTT handling
  if (wifiConnected) {
    if (!mqttConnected) {
      if (now - lastMqttRetryMs >= MQTT_RETRY_INTERVAL_MS) {
        lastMqttRetryMs = now;
        connectMQTT();
      }
    } else {
      mqttClient.loop();
    }
  }
  
  // NTP time update
  if (now - lastNtpUpdateMs >= NTP_UPDATE_INTERVAL_MS) {
    lastNtpUpdateMs = now;
    configTime(TIMEZONE_OFFSET_SECONDS, 0, "pool.ntp.org", "time.nist.gov");
  }
  
  // Run scheduler
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
  
  // Health log
  if (now - lastHealthLogMs >= HEALTH_LOG_INTERVAL_MS) {
    lastHealthLogMs = now;
    Serial.print("Health: uptime_ms=");
    Serial.print(now);
    Serial.print(" wifi=");
    Serial.print(wifiConnected ? "connected" : "disconnected");
    Serial.print(" mqtt=");
    Serial.print(mqttConnected ? "connected" : "disconnected");
    Serial.print(" rssi=");
    Serial.println(wifiConnected ? WiFi.RSSI() : 0);
  }
  
  delay(1);
}

// ===== WIFI FUNCTIONS =====
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
  
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection failed");
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
  snprintf(clientId, sizeof(clientId), "tankctl-esp32-%s", tankId);
  
  Serial.print("Connecting to MQTT broker: ");
  Serial.print(MQTT_SERVER);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  
  if (mqttClient.connect(clientId)) {
    Serial.println("MQTT connected");
    
    // Subscribe to command topic
    mqttClient.subscribe(topicCommand);
    Serial.print("Subscribed to: ");
    Serial.println(topicCommand);
    
    // Publish initial states
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
  
  // Save to Preferences
  saveSchedule();

  Serial.print("Schedule updated: ON ");
  Serial.print(onTime);
  Serial.print(", OFF ");
  Serial.println(offTime);
  
  publishReportedState();
}

void handleRebootDevice() {
  Serial.println("Reboot command received");
  
  // Publish final state before reset
  publishReportedState();
  publishHeartbeat();
  
  // Give MQTT a window to flush
  unsigned long flushStart = millis();
  while (millis() - flushStart < 300) {
    mqttClient.loop();
    delay(10);
  }
  
  Serial.println("Rebooting now...");
  Serial.flush();
  delay(100);
  
  // ESP32 reboot
  ESP.restart();
}

void publishFirmwareStatus(const char* status, const char* version, const char* error = nullptr) {
  if (!mqttClient.connected()) {
    return;
  }
  
  char statusTopic[64];
  snprintf(statusTopic, sizeof(statusTopic), "tankctl/%s/firmware_status", tankId);
  
  StaticJsonDocument<256> doc;
  doc["status"] = status;
  doc["version"] = version;
  doc["timestamp"] = millis();
  if (error) {
    doc["error"] = error;
  }
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  mqttClient.publish(statusTopic, buffer);
  
  Serial.print("[Firmware Status] ");
  Serial.println(buffer);
}

void handleUpdateFirmware(JsonDocument& doc) {
  if (!doc.containsKey("url")) {
    Serial.println("update_firmware: missing url");
    return;
  }
  
  const char* url = doc["url"];
  const char* version = doc.containsKey("version") ? (const char*)doc["version"] : "unknown";
  
  Serial.print("[Firmware Update] URL: ");
  Serial.println(url);
  Serial.print("[Firmware Update] Version: ");
  Serial.println(version);
  
  // Publish status before starting update
  publishFirmwareStatus("updating", version);
  
  // Small delay to ensure MQTT message is sent
  delay(500);
  mqttClient.loop();
  
  // Start firmware update
  updateFirmwareFromURL(url, version);
}

void updateFirmwareFromURL(const char* url, const char* version) {
  if (!WiFi.isConnected()) {
    Serial.println("[Firmware Update] WiFi not connected, cannot update");
    publishFirmwareStatus("failed", version, "WiFi not connected");
    return;
  }
  
  HTTPClient http;
  
  Serial.print("[Firmware Update] Connecting to: ");
  Serial.println(url);
  
  http.begin(url);
  int httpCode = http.GET();
  
  Serial.print("[Firmware Update] HTTP response code: ");
  Serial.println(httpCode);
  
  if (httpCode != HTTP_CODE_OK) {
    Serial.print("[Firmware Update] Failed to download firmware: ");
    Serial.println(httpCode);
    publishFirmwareStatus("failed", version, "HTTP download failed");
    http.end();
    return;
  }
  
  int contentLength = http.getSize();
  Serial.print("[Firmware Update] Firmware size: ");
  Serial.print(contentLength);
  Serial.println(" bytes");
  
  if (contentLength <= 0) {
    Serial.println("[Firmware Update] Invalid content length");
    publishFirmwareStatus("failed", version, "Invalid content length");
    http.end();
    return;
  }
  
  // Check if we have enough free space
  if (!Update.begin(contentLength)) {
    Serial.println("[Firmware Update] Not enough space for firmware update");
    publishFirmwareStatus("failed", version, "Not enough space");
    http.end();
    return;
  }
  
  Serial.println("[Firmware Update] Starting firmware update...");
  
  // Stream the firmware data
  WiFiClient* stream = http.getStreamPtr();
  size_t written = 0;
  uint8_t buffer[4096];
  
  while (http.connected() && (written < contentLength)) {
    size_t available = stream->available();
    
    if (available) {
      int bytesRead = stream->readBytes(buffer, min((int)available, (int)sizeof(buffer)));
      
      if (Update.write(buffer, bytesRead) != bytesRead) {
        Serial.println("[Firmware Update] Write failed");
        Update.abort();
        publishFirmwareStatus("failed", version, "Write failed");
        http.end();
        return;
      }
      
      written += bytesRead;
      int percent = (written / (contentLength / 100));
      
      // Log progress every 10%
      static int lastPercent = 0;
      if (percent != lastPercent && percent % 10 == 0) {
        Serial.print("[Firmware Update] Progress: ");
        Serial.print(percent);
        Serial.println("%");
        lastPercent = percent;
      }
    }
    
    delay(1);
  }
  
  http.end();
  
  if (written != contentLength) {
    Serial.print("[Firmware Update] Incomplete download: ");
    Serial.print(written);
    Serial.print(" / ");
    Serial.println(contentLength);
    Update.abort();
    publishFirmwareStatus("failed", version, "Incomplete download");
    return;
  }
  
  if (!Update.end()) {
    Serial.print("[Firmware Update] Error finalizing update: ");
    Serial.println(Update.getError());
    publishFirmwareStatus("failed", version, "Update finalization failed");
    return;
  }
  
  if (!Update.isFinished()) {
    Serial.println("[Firmware Update] Update not finished");
    publishFirmwareStatus("failed", version, "Update not finished");
    return;
  }
  
  Serial.println("[Firmware Update] Update successful! Rebooting...");
  publishFirmwareStatus("success", version);
  
  // Give time for MQTT message to be sent
  delay(1000);
  
  ESP.restart();
}

// ===== LIGHT CONTROL =====
void setLight(bool state) {
  lightState = state;
  int pinState = state ? LOW : HIGH;
  
  Serial.print("Setting light to: ");
  Serial.println(state ? "ON (GPIO LOW)" : "OFF (GPIO HIGH)");
  
  digitalWrite(RELAY_PIN, pinState);
  
  Serial.print("Light state: ");
  Serial.println(state ? "ON" : "OFF");
}

// ===== TELEMETRY =====
void publishTelemetry() {
  if (!mqttClient.connected()) {
    return;
  }
  
#if USE_RANDOM_TEMP
  // Generate random temperature for testing (no sensor required)
  static unsigned long lastRandomTempMs = 0;
  unsigned long now = millis();
  
  if (now - lastRandomTempMs >= TELEMETRY_INTERVAL_MS) {
    lastRandomTempMs = now;
    
    // Generate random float between TEMP_MIN and TEMP_MAX
    float randTemp = TEMP_MIN + (random(0, 1000) / 1000.0f) * (TEMP_MAX - TEMP_MIN);
    temperature = randTemp;
    
    Serial.print("Telemetry (random): temp=");
    Serial.print(temperature);
    Serial.println("°C");
    
    StaticJsonDocument<128> doc;
    doc["temperature"] = temperature;
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    mqttClient.publish(topicTelemetry, buffer);
  }
#else
  // Use real DS18B20 sensor
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
  
  // Read completed conversion
  float tempReading = sensors.getTempCByIndex(0);
  sensors.requestTemperatures();
  tempRequestMs = now;
  tempConversionInProgress = true;
  
  // Validate sensor reading
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
    
    // Publish warning
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
#endif
}

void publishHeartbeat() {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<128> doc;
  doc["status"] = "online";
  doc["uptime_ms"] = millis();
  doc["rssi"] = WiFi.RSSI();
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["chip"] = "ESP32";
  doc["free_heap"] = ESP.getFreeHeap();
  
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

// ===== SCHEDULER =====
void runSchedule() {
  if (!scheduleEnabled) {
    return;
  }
  
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  int currentHour = timeinfo->tm_hour;
  int currentMinute = timeinfo->tm_min;
  
  // Check if it's time to turn light on
  if (currentHour == scheduleOnHour && currentMinute == scheduleOnMinute) {
    if (!lightState) {
      setLight(true);
      publishReportedState();
    }
  }
  
  // Check if it's time to turn light off
  if (currentHour == scheduleOffHour && currentMinute == scheduleOffMinute) {
    if (lightState) {
      setLight(false);
      publishReportedState();
    }
  }
}

// ===== PREFERENCES (NVS Storage) =====
void loadConfig() {
  // Load tank ID
  String savedTankId = preferences.getString("tank_id", DEFAULT_TANK_ID);
  strncpy(tankId, savedTankId.c_str(), TANK_ID_MAX_LEN - 1);
  tankId[TANK_ID_MAX_LEN - 1] = 0;
  
  // Load device secret (if exists, device is registered)
  String savedSecret = preferences.getString("device_secret", "");
  if (savedSecret.length() > 0) {
    strncpy(deviceSecret, savedSecret.c_str(), DEVICE_SECRET_MAX_LEN - 1);
    deviceSecret[DEVICE_SECRET_MAX_LEN - 1] = 0;
    deviceRegistered = true;
    Serial.println("Device already registered (secret found in NVS)");
  } else {
    deviceRegistered = false;
    Serial.println("Device not registered yet (no secret in NVS)");
  }
  
  // Load schedule
  scheduleOnHour = preferences.getInt("sched_on_h", 18);
  scheduleOnMinute = preferences.getInt("sched_on_m", 0);
  scheduleOffHour = preferences.getInt("sched_off_h", 6);
  scheduleOffMinute = preferences.getInt("sched_off_m", 0);
  scheduleEnabled = preferences.getBool("sched_enabled", false);
  
  Serial.print("Loaded config from NVS. Tank ID: ");
  Serial.println(tankId);
  Serial.print("Schedule: ");
  Serial.print(scheduleOnHour);
  Serial.print(":");
  Serial.print(scheduleOnMinute);
  Serial.print(" - ");
  Serial.print(scheduleOffHour);
  Serial.print(":");
  Serial.print(scheduleOffMinute);
  Serial.print(" (");
  Serial.print(scheduleEnabled ? "enabled" : "disabled");
  Serial.println(")");
}

void saveSchedule() {
  preferences.putInt("sched_on_h", scheduleOnHour);
  preferences.putInt("sched_on_m", scheduleOnMinute);
  preferences.putInt("sched_off_h", scheduleOffHour);
  preferences.putInt("sched_off_m", scheduleOffMinute);
  preferences.putBool("sched_enabled", scheduleEnabled);
  
  Serial.println("Schedule saved to NVS");
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
  
  // Build JSON payload
  StaticJsonDocument<128> requestDoc;
  requestDoc["device_id"] = tankId;
  
  String payload;
  serializeJson(requestDoc, payload);
  
  // Send HTTP POST request
  String request = "POST ";
  request += REGISTRATION_ENDPOINT;
  request += " HTTP/1.1\r\n";
  request += "Host: ";
  request += REGISTRATION_SERVER;
  request += ":";
  request += REGISTRATION_PORT;
  request += "\r\n";
  request += "Content-Type: application/json\r\n";
  request += "Content-Length: ";
  request += payload.length();
  request += "\r\n";
  request += "Connection: close\r\n";
  request += "\r\n";
  request += payload;
  
  Serial.print("[Registration] Sending request... ");
  httpClient.print(request);
  Serial.println("done");
  
  // Wait for response
  unsigned long timeout = millis() + 5000;  // 5 second timeout
  String response = "";
  String statusLine = "";
  
  while (httpClient.connected() || httpClient.available()) {
    if (millis() > timeout) {
      Serial.println("[Registration] Response timeout");
      break;
    }
    
    if (httpClient.available()) {
      char c = httpClient.read();
      response += c;
    }
    delay(1);
  }
  
  httpClient.stop();
  
  // Extract HTTP status code from response
  int statusCode = 200;
  if (response.indexOf("HTTP/1.1") != -1) {
    int spacePos = response.indexOf(" ");
    if (spacePos != -1) {
      String statusStr = response.substring(spacePos + 1, spacePos + 4);
      statusCode = statusStr.toInt();
    }
  }
  
  Serial.print("[Registration] HTTP Status: ");
  Serial.println(statusCode);
  
  // Parse response
  if (response.length() > 0) {
    // Find JSON part (skip HTTP headers)
    int jsonStart = response.indexOf("\r\n\r\n");
    if (jsonStart != -1) {
      jsonStart += 4;  // Skip "\r\n\r\n"
      String jsonStr = response.substring(jsonStart);
      
      Serial.print("[Registration] Raw response: ");
      Serial.println(jsonStr);
      
      StaticJsonDocument<512> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, jsonStr);
      
      if (!error) {
        if (statusCode == 409) {
          // Device already registered - mark as registered without secret
          Serial.println("[Registration] ✓ Device already registered on backend (409 Conflict)");
          deviceRegistered = true;
          // Try to load secret from storage in case it exists
        } else if (responseDoc.containsKey("device_secret")) {
          String secret = responseDoc["device_secret"];
          strncpy(deviceSecret, secret.c_str(), DEVICE_SECRET_MAX_LEN - 1);
          deviceSecret[DEVICE_SECRET_MAX_LEN - 1] = 0;
          
          // Save to NVS
          preferences.putString("device_secret", secret);
          deviceRegistered = true;
          
          Serial.println("[Registration] ✓ Device registered successfully!");
          Serial.print("[Registration] Device Secret (first 16 chars): ");
          Serial.print(secret.substring(0, 16));
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
