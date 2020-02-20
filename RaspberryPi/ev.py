#!/usr/bin/python3

import os
import time

import config
import motionSensor
import relayServer
import telegram
import webcam
import wificam


class Source:
    MOTION = 0
    MANUAL = 1

def currentTime():
    return int(time.time())

class Command:
    RELAY_ON              = "ON"
    RELAY_OFF             = "OFF"
    TAKE_PHOTO            = "PHOTO"
    DISABLE_MOTION_SENSOR = "MOFF"
    ENABLE_MOTION_SENSOR  = "MON"


class Commander:

    def __init__(self):
        self._telegram = telegram.Telegram(config.telegramURL, config.telegramToken, config.telegramChatId)
        self._relayServer = relayServer.RelayServer()
        self._wifiCam = wificam.WifiCam()

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
                        print("ON")
                        self._switchOn(Source.MANUAL)

                    elif msg == Command.RELAY_OFF:
                        print("OFF")
                        self._switchOff()

                    elif msg == Command.TAKE_PHOTO:
                        print("PHOTO")
                        self._takePhoto()

                    elif msg == Command.DISABLE_MOTION_SENSOR:
                        print("MOFF")
                        self._motionSensor.disable()
                        self._telegram.sendMessage("Done")

                    elif msg == Command.ENABLE_MOTION_SENSOR:
                        print("MON")
                        self._motionSensor.enable()
                        self._telegram.sendMessage("Done")
            else:
                msgCnt += 1

            if self._shouldTurnSwitchOff():
                print("OFF")
                self._switchOff()

            time.sleep(0.1)

    def _sendPhoto(self):
        photo = self._wifiCam.takePhoto()

        self._telegram.sendPhoto(photo)


    def _sendVideo(self):
        videoFile = webcam.shootVideo()

        f = open(videoFile, "rb")

        self._telegram.sendVideo(f)

        f.close()

        os.remove(videoFile)

    def _takePhoto(self):
        #self._relayServer.sendCommand("ON")

        #self._sendPhoto()
        video = self._wifiCam.record()

        self._telegram.sendVideo(video)
        #if self._switchOnTs == 0: self._relayServer.sendCommand("OFF")

    def _switchOn(self, source):
        #if source == Source.MOTION and self._switchOnTs > 0 : return

        self._relayServer.sendCommand("ON")
        self._switchOnTs = currentTime()

        if source == Source.MOTION:
            self._sendVideo()

    def _switchOff(self):
        self._relayServer.sendCommand("OFF")
        self._switchOnTs = 0
        self._telegram.sendMessage("OFF")

    def _shouldTurnSwitchOff(self):
        return self._switchOnTs > 0 and currentTime() - self._switchOnTs > 10 * 60


if __name__ == "__main__":

    commander = Commander()
    commander.start()

