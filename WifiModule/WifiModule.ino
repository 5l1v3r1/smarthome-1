#include <WiFi.h>

#define WIFI_SSID     "Kablonet Netmaster-CA0B-G"
#define WIFI_PASSWORD "ce1a5f35"

#define RELAY_PIN 15

#define COMM_RETRY_WAIT 500
#define COMM_RETRY_LIMIT 5
#define PING_TIMEOUT 5000
#define PING_RETRY_WAIT 10000

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
  Serial.begin(9600);

  while(!Serial);

  Serial.println("Starting...");

  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  if (!client && !client.connect("192.168.0.12", 42024)) {
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
  while(client.available()) {
      dataReceived = true;
      String line = client.readStringUntil('\n');

      Serial.println(line);

      if (line.equals("ON")) digitalWrite(RELAY_PIN, LOW);
      else if (line.equals("OFF")) digitalWrite(RELAY_PIN, HIGH);
      else if (line.equals("PONG")) pingTimer = 0;
      
  }

  if (pingTimer == 0 && !dataReceived && (millis() - lastPing) > PING_RETRY_WAIT) {
    client.print(String("PING\n"));
    Serial.println("PING");
    pingTimer = millis();
    lastPing = pingTimer;
  } else if (pingTimer > 0 && !dataReceived && (millis() - pingTimer) > PING_TIMEOUT) {
    Serial.println("Connection is not alive!");
    pingTimer = 0;
    client.stop();
  }
}
