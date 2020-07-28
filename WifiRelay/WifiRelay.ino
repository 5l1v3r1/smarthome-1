#include <WiFi.h>
#include "config.h"

#define RELAY_PIN 15

#define COMM_RETRY_WAIT 500
#define COMM_RETRY_LIMIT 5
#define PING_TIMEOUT 5000
#define PING_RETRY_WAIT 10000

#define PING_CMD 0x20
#define PONG_CMD 0x21
#define ON_CMD   0x25
#define OFF_CMD  0x26

WiFiClient client;
unsigned int nc = 0;
unsigned long pingTimer = 0;
unsigned long lastPing = 0;

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Trying to connect to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
      nc++;
      if (nc > COMM_RETRY_LIMIT) {
        nc = 0;
        digitalWrite(RELAY_PIN, HIGH);
      }
      delay(COMM_RETRY_WAIT);
  }

  nc = 0;
  Serial.println("Connected to WiFi!");
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  Serial.begin(115200);

  while(!Serial);

  Serial.println("Starting...");

  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  if (!client && !client.connect(REMOTE_ADDR, 42024)) {
      Serial.println("Connection failed");
      nc++;
      if (nc > COMM_RETRY_LIMIT) {
        nc = 0;
        digitalWrite(RELAY_PIN, HIGH);
      }
      delay(COMM_RETRY_WAIT);
      return;
  }
  nc = 0;
  
  bool dataReceived = false;
  uint8_t buffer[1];
  while(client.available()) {
      dataReceived = true;
      int n = client.read(buffer, 1);

      if (n != 1) {
        continue;
      }

      switch(buffer[0]) {
        case PONG_CMD:
          Serial.println("PONG");
          pingTimer=0;
          break;
          
        case ON_CMD:
          Serial.println("ON");
          digitalWrite(RELAY_PIN, LOW);
          break;
          
        case OFF_CMD:
          Serial.println("OFF");
          digitalWrite(RELAY_PIN, HIGH);
          break;
            
      }
      
  }

  if (pingTimer == 0 && !dataReceived && (millis() - lastPing) > PING_RETRY_WAIT) {
    client.write(PING_CMD);
    Serial.println("PING");
    pingTimer = millis();
    lastPing = pingTimer;
  } else if (pingTimer > 0 && !dataReceived && (millis() - pingTimer) > PING_TIMEOUT) {
    Serial.println("Connection is not alive!");
    pingTimer = 0;
    client.stop();
  }
}
