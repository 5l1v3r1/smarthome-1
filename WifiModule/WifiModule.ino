#include <WiFi.h>

#define WIFI_SSID     "Kablonet Netmaster-CA0B-G"
#define WIFI_PASSWORD "ce1a5f35"

#define RELAY_PIN 15

WiFiClient client;

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
  }

  Serial.println("Connected!");
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  Serial.begin(9600);

  while(!Serial);

  Serial.println("Starting...");

  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  if (!client && !client.connect("192.168.0.12", 42024)) {
      Serial.println("connection failed");
      delay(2000);
      return;
  }

  
  while(client.available()) {
      Serial.println("connection");
      String line = client.readStringUntil('\n');

      Serial.println(line);

      if (line.equals("ON")) digitalWrite(RELAY_PIN, LOW);
      else if (line.equals("OFF")) digitalWrite(RELAY_PIN, HIGH);
  }

}
