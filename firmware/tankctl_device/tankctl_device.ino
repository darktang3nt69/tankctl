// ===== CONFIG =====
#define WIFI_SSID "EMPIRE_2.4G"
#define WIFI_PASSWORD "30379718"

#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883

#define DEFAULT_TANK_ID "tank1"
#define RELAY_PIN 5
#define ONE_WIRE_PIN 6

#define TELEMETRY_INTERVAL_MS 5000UL
#define HEARTBEAT_INTERVAL_MS 30000UL
#define WIFI_RETRY_INTERVAL_MS 5000UL
#define MQTT_RETRY_INTERVAL_MS 3000UL

// EEPROM addresses
#define EEPROM_ADDR_TANK_ID 0
#define EEPROM_ADDR_SCHEDULE_ON_HOUR 32
#define EEPROM_ADDR_SCHEDULE_ON_MINUTE 34
#define EEPROM_ADDR_SCHEDULE_OFF_HOUR 36
#define EEPROM_ADDR_SCHEDULE_OFF_MINUTE 38
#define EEPROM_ADDR_SCHEDULE_ENABLED 40
#define EEPROM_ADDR_INIT_FLAG 41
#define EEPROM_INIT_FLAG 0xA5

#define TANK_ID_MAX_LEN 32

// ===== LIBRARIES =====
#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
#include <NTPClient.h>
#include <WiFiUdp.h>

// ===== GLOBAL STATE =====
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);

char tankId[TANK_ID_MAX_LEN] = {0};
bool lightState = false;
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

char topicCommand[64];
char topicReported[64];
char topicTelemetry[64];
char topicHeartbeat[64];

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("TankCtl Device Starting...");
  
  // Initialize relay pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  // Load configuration from EEPROM
  loadConfig();
  
  // Build MQTT topics
  buildTopics();
  
  // Initialize temperature sensor
  sensors.begin();
  
  // Connect WiFi
  connectWiFi();
  
  // Synchronize time
  timeClient.begin();
  Serial.println("Synchronizing time with NTP...");
  timeClient.update();
  
  // Connect MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  connectMQTT();
  
  Serial.println("TankCtl Device Ready");
}

// ===== MAIN LOOP =====
void loop() {
  unsigned long now = millis();
  
  // Ensure WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiRetryMs >= WIFI_RETRY_INTERVAL_MS) {
      lastWifiRetryMs = now;
      connectWiFi();
    }
  }
  
  // Ensure MQTT connection
  if (!mqttClient.connected()) {
    if (now - lastMqttRetryMs >= MQTT_RETRY_INTERVAL_MS) {
      lastMqttRetryMs = now;
      connectMQTT();
    }
  } else {
    mqttClient.loop();
  }
  
  // Update NTP time
  timeClient.update();
  
  // Run local scheduler
  runSchedule();
  
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
}

// ===== WIFI FUNCTIONS =====
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
  
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(300);
    Serial.print(".");
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
  
  // Save to EEPROM
  saveSchedule();
  
  Serial.print("Schedule updated: ON ");
  Serial.print(onTime);
  Serial.print(", OFF ");
  Serial.println(offTime);
  
  publishReportedState();
}

// ===== LIGHT CONTROL =====
void setLight(bool state) {
  lightState = state;
  digitalWrite(RELAY_PIN, state ? HIGH : LOW);
  
  Serial.print("Light: ");
  Serial.println(state ? "ON" : "OFF");
}

// ===== TELEMETRY =====
void publishTelemetry() {
  if (!mqttClient.connected()) {
    return;
  }
  
  // Read temperature
  sensors.requestTemperatures();
  temperature = sensors.getTempCByIndex(0);
  
  // Build JSON
  StaticJsonDocument<128> doc;
  doc["temperature"] = temperature;
  
  char buffer[128];
  serializeJson(doc, buffer);
  
  mqttClient.publish(topicTelemetry, buffer);
  
  Serial.print("Telemetry: temp=");
  Serial.print(temperature);
  Serial.println("°C");
}

void publishHeartbeat() {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<64> doc;
  doc["status"] = "online";
  
  char buffer[64];
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
  
  int currentHour = timeClient.getHours();
  int currentMinute = timeClient.getMinutes();
  
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
    
    saveTankId();
    saveSchedule();
    EEPROM.write(EEPROM_ADDR_INIT_FLAG, EEPROM_INIT_FLAG);
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
