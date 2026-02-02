#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- USER CONFIGURATION ---
const char* ssid = "Bbox-093DE834";       // Your Hotspot Name (That just worked)
const char* password = "zHv6Wh9aXiMq7iA4P1";  // Your Hotspot Password

const char* mqtt_server = "broker.hivemq.com";
const char* mqtt_topic = "mahdi/iot/scan";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("\n--- FINAL IOT PROJECT START ---");

  // 1. Connect to WiFi
  Serial.printf("Connecting to %s", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[SUCCESS] WiFi Connected!");
  
  // 2. Setup MQTT
  client.setServer(mqtt_server, 1883);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5s");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // --- STEP 1: SCAN ---
  Serial.println("\n[1] Scanning WiFi...");
  int n = WiFi.scanNetworks();
  
  if (n == 0) {
    Serial.println("No networks found.");
  } else {
    // --- STEP 2: JSON ---
    Serial.printf("[2] Found %d networks. Creating JSON...\n", n);
    StaticJsonDocument<4096> doc;
    JsonArray scans = doc.createNestedArray("scans");

    for (int i = 0; i < n; ++i) {
      JsonObject scanObj = scans.createNestedObject();
      scanObj["mac"]  = WiFi.BSSIDstr(i);
      scanObj["rssi"] = WiFi.RSSI(i);
      scanObj["ssid"] = WiFi.SSID(i);
    }

    String payload;
    serializeJson(doc, payload);

    // --- STEP 3: PUBLISH ---
    Serial.print("[3] Publishing to MQTT... ");
    // Make sure message isn't too big for buffer (increase buffer if needed)
    client.setBufferSize(4096); 
    
    if (client.publish(mqtt_topic, payload.c_str())) {
      Serial.println("SUCCESS! Data sent.");
    } else {
      Serial.println("FAILED. (Payload might be too big)");
    }
  }

  // Wait 30 seconds
  Serial.println("Waiting 5 seconds...\n");
  delay(500);
}