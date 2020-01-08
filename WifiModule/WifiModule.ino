#include <WiFi.h>

#define WIFI_SSID     "Kablonet Netmaster-CA0B-A"
#define WIFI_PASSWORD "ce1a5f35"

#define RELAY_PIN 15

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

   WiFiClient client;
  if (!client.connect("192.168.0.12", 42024)) {
      Serial.println("connection failed");
      delay(2000);
      return;
  }

  while(client.available()) {
      String line = client.readStringUntil('\n');

      if (line.equals("ON")) digitalWrite(RELAY_PIN, LOW);
      else if (line.equals("OFF")) digitalWrite(RELAY_PIN, HIGH);
  }

}
