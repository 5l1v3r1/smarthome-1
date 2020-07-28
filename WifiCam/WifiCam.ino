#include <HTTPClient.h>
#include <WiFi.h>
#include "config.h"
#include "esp_camera.h"
#include "soc/soc.h"           // Disable brownour problems
#include "soc/rtc_cntl_reg.h"  // Disable brownour problems
#include "driver/rtc_io.h"

#define RECORD_TIME 10 //10s

#define COMM_RETRY_WAIT 500
#define COMM_RETRY_LIMIT 5
#define PING_TIMEOUT 5000
#define PING_RETRY_WAIT 10000

#define PING_CMD   0x20
#define PONG_CMD   0x21
#define PHOTO_CMD  0x22
#define VIDEO_CMD  0x23
#define STREAM_CMD 0x24
#define MON_CMD    0x27
#define MOFF_CMD   0x28

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define PIR_GPIO_NUM      14

WiFiClient client;
WiFiClient streamClient;

unsigned int nc = 0;
unsigned long pingTimer = 0;
unsigned long lastPing = 0;

bool connectedToRemote = false;

bool sensorEnabled = true;

unsigned long lastTriggered = 0;
#define TRIGGER_TIMEOUT 10 // in seconds


void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Trying to connect to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
      nc++;
      if (nc > COMM_RETRY_LIMIT) {
        //digitalWrite(RELAY_PIN, HIGH);
        nc = 0;
      }
      delay(COMM_RETRY_WAIT);
  }

  nc = 0;
  Serial.println("Connected to WiFi!");
}

void setup() {
  Serial.begin(115200);

  while(!Serial);

  Serial.println("Starting...");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG; 
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA; // FRAMESIZE_ + QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
    config.jpeg_quality = 8;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Init Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  connectWiFi();

  pinMode(PIR_GPIO_NUM, INPUT);

}

void takePhotoAndSend() {
  camera_fb_t * fb = NULL;
  
  fb = esp_camera_fb_get();  
  if(!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  client.write(PHOTO_CMD);

  client.write((uint8_t) ((fb->len >> 24) & 0xff));
  client.write((uint8_t) ((fb->len >> 16) & 0xff));
  client.write((uint8_t) ((fb->len >> 8) & 0xff ));
  client.write((uint8_t) (fb->len & 0xff));  

  Serial.println("Sending photo");
  client.write(fb->buf, fb->len);
  Serial.println("Photo sent");
  Serial.println(fb->len);

  esp_camera_fb_return(fb);
  
}


void recordAndSend() {
  unsigned long startTime = millis();

  client.write(VIDEO_CMD);

  while (millis() - startTime < RECORD_TIME * 1000) {
    camera_fb_t * fb = NULL;
  
    fb = esp_camera_fb_get();  
    if(!fb) {
      Serial.println("Camera capture failed");
      return;
    }
  
    client.write((uint8_t) ((fb->len >> 24) & 0xff));
    client.write((uint8_t) ((fb->len >> 16) & 0xff));
    client.write((uint8_t) ((fb->len >> 8) & 0xff ));
    client.write((uint8_t) (fb->len & 0xff));  
  
    client.write(fb->buf, fb->len);
    
    esp_camera_fb_return(fb);
    
  }

  client.write((uint8_t) 0x00);
  client.write((uint8_t) 0x00);
  client.write((uint8_t) 0x00);
  client.write((uint8_t) 0x00);
}

void stream() {

  if (!streamClient.connected()) {
    Serial.println("There is no connection to stream server");
    return;
  }

  while (streamClient.connected()) {
    camera_fb_t * fb = NULL;
  
    fb = esp_camera_fb_get();  
    if(!fb) {
      Serial.println("Camera capture failed");
      streamClient.stop();
      return;
    }

    streamClient.write((uint8_t) ((fb->len >> 24) & 0xff));
    streamClient.write((uint8_t) ((fb->len >> 16) & 0xff));
    streamClient.write((uint8_t) ((fb->len >> 8) & 0xff ));
    streamClient.write((uint8_t) (fb->len & 0xff));
  
    streamClient.write(fb->buf, fb->len);
    
    esp_camera_fb_return(fb);
  }

  streamClient.stop();
}

bool hasMotion() {
  int val = digitalRead(PIR_GPIO_NUM);

  //Serial.println(val);

  return val == 1;
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  if (!connectedToRemote && !client.connect(REMOTE_ADDR, 42025)) {
      Serial.println("Connection failed");
      nc++;
      if (nc > COMM_RETRY_LIMIT) {
        nc = 0;
        //digitalWrite(RELAY_PIN, HIGH);
      }
      delay(COMM_RETRY_WAIT);
      return;
  }
  nc = 0;
  connectedToRemote = true;

  if (!streamClient.connected()) {
    streamClient.connect(REMOTE_ADDR, 42026);  
  }

  if (sensorEnabled && hasMotion()) {
    if (lastTriggered == 0 || millis() - lastTriggered > TRIGGER_TIMEOUT * 1000) {
      Serial.println("intruder alert!!");
      lastTriggered = millis();
      takePhotoAndSend();
    }

  }
  
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
          
        case PHOTO_CMD:
          Serial.println("PHOTO");
          takePhotoAndSend();
          break;

        case VIDEO_CMD:
          Serial.println("VIDEO");
          recordAndSend();
          break;
          
        case STREAM_CMD:
          Serial.println("STREAM");
          stream();
          break;

        case MON_CMD:
          Serial.println("MON");
          sensorEnabled = true;
          break;

        case MOFF_CMD:
          Serial.println("MOFF");
          sensorEnabled = false;
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
    connectedToRemote = false;
    client.stop();
  }

}
