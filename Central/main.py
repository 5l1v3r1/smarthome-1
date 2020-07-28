#!/usr/bin/python3

import time

import config
import relayServer
import telegram
import wificam

def currentTime():
    return int(time.time())

class Command:
    RELAY_ON              = "ON"
    RELAY_OFF             = "OFF"
    TAKE_PHOTO            = "PHOTO"
    RECORD_VIDEO          = "VIDEO"
    DISABLE_MOTION_SENSOR = "MOFF"
    ENABLE_MOTION_SENSOR  = "MON"
    STREAM                = "STRM"


class Commander:

    def __init__(self):
        self._telegram = telegram.Telegram(config.telegramURL, config.telegramToken, config.telegramChatId)
        self._relayServer = relayServer.RelayServer()
        self._wifiCam = wificam.WifiCam(self._telegram)

        self._switchOnTs = 0

    def start(self):
        self._relayServer.start()
        self._wifiCam.start()

        msgCnt = 0
        while True:
            if msgCnt == 10:
                msgCnt = 0
                msgs = self._telegram.getMessages()

                for msg in msgs:
                    if msg == Command.RELAY_ON:
                        print("[+] Switch on message received.")
                        self._switchOn()

                    elif msg == Command.RELAY_OFF:
                        print("[+] Switch off message received.")
                        self._switchOff()

                    elif msg == Command.TAKE_PHOTO:
                        print("[+] Take phote message received.")
                        self._takePhoto()

                    elif msg == Command.RECORD_VIDEO:
                        print("[+] Record video message received.")
                        self._sendVideo()

                    elif msg == Command.DISABLE_MOTION_SENSOR:
                        print("[+] Disable motion sensor message received.")
                        self._wifiCam.sensorOff()
                        self._telegram.sendMessage("Done")

                    elif msg == Command.ENABLE_MOTION_SENSOR:
                        print("[+] Enable motion sensor message received.")
                        self._wifiCam.sensorOn()
                        self._telegram.sendMessage("Done")

            else:
                msgCnt += 1

            if self._shouldTurnSwitchOff():
                print("[+] Turning switch off due to timeout...")
                self._switchOff()

            time.sleep(0.1)

    def _sendPhoto(self):
        self._wifiCam.takePhoto()

    def _sendVideo(self):
        video = self._wifiCam.record()

        self._telegram.sendVideo(video)

    def _takePhoto(self):
        self._sendPhoto()

    def _switchOn(self):
        self._relayServer.switchOn()
        self._switchOnTs = currentTime()

    def _switchOff(self):
        self._relayServer.switchOff()
        self._switchOnTs = 0
        self._telegram.sendMessage("OFF")

    def _shouldTurnSwitchOff(self):
        return self._switchOnTs > 0 and currentTime() - self._switchOnTs > 10 * 60


if __name__ == "__main__":
    commander = Commander()
    commander.start()

