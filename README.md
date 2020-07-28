# smarthome
![smarthome](https://github.com/paddlesteamer/smarthome/workflows/smarthome/badge.svg?branch=master)

smarthome is a personalized smart home project controlled with [Telegram](https://telegram.org/). Currently, it has three components but has flexiblity for more.

## Components
### Central

This is the central module and controller of *smarthome*. All other components should be connected and report to this module. This may be installed on any server with a public ip like a RaspberryPi or a VPS. 

### WifiRelay

This is the remote controlled relay component. Any device working with current lower than **2A**-(will be edited later) can be connected to this component for remote activation/deactivation.

This component is made of from a 220V AC to 5V DC voltage converter and a relay connected to a [ESP32 Dev Module](https://circuits4you.com/2018/12/31/esp32-devkit-esp32-wroom-gpio-pinout/)

### WifiCam

This [ESP32+cam](https://www.robotistan.com/esp32-cam-wifi-bluetooth-gelistirme-karti-ov2640-kamera-modul) module has a PIR motion sensor, a relay for enabling light source(camera needs light) and a camera on it. It dispatches an alarm if it detects a motion with PIR sensor. It has capabilities to take a photo or live stream on demand.

## Setup
### Central

First put the **Central** folder on your server. Rename `config.example.py`

```sh
mv config.example.py config.py
```

and fill related fields with your telegram bot info. Then just run:

```sh
python3 main.py
``` 

### WifiRelay

First rename `config.example.h` 

```sh
mv config.example.h config.h
```

and fill WiFi authorization fields and **Central**'s public ip in related fields.
 
Install espressif esp32 plugin to your Arduine IDE. [Here](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/) is a nice tutorial to do so. 

Open the **WifiRelay** folder with your Arduino IDE. From *Tools->Board* select `DOIT ESP32 DEVKIT V1` and load the code to the device.

### WifiCam

First rename `config.example.h` 

```sh
mv config.example.h config.h
```

and fill WiFi authorization fields and **Central**'s public ip in related fields.
 
Open the **WifiCam** folder with your Arduino IDE. From *Tools->Board* select `AI Thinker ESP32-CAM` and load the code to the device.

## Usage

There are several commands to control the devices. The commands may be sent with telegram app as messages.

- **ON:** It activates relay on **WifiRelay** module.

- **OFF:** It disables relay on **WifiRelay** module.

- **MON:** It enables motion sensor on **WifiCam** module.

- **MOFF:** It disables motion sensor on **WifiCam** module.

- **PHOTO:** It tells **WifiCam** to take photo and send it via telegram.

- **STRM:** It tells **WifiCam** to start a live stream and send the stream link via telegram.

**Note:** All commands are case insensitive and motion sensor is enabled by default.
