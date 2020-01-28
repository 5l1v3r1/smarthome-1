#!/usr/bin/python3

import os
import time

import config
import motionSensor
import relayServer
import telegram
import webcam


class Source:
    MOTION = 0
    MANUAL = 1

def currentTime():
    return int(time.time())

def sendPhoto():
    global telegram

    photoFile = webcam.takePhoto()

    f = open(photoFile, "rb")

    telegram.sendPhoto(f)

    f.close()

    os.remove(photoFile)
    
    
def sendVideo():
    global telegram

    videoFile = webcam.shootVideo()

    f = open(videoFile, "rb")
    
    telegram.sendVideo(f)

    f.close()

    os.remove(videoFile)
    
def takePhoto():
    relayServer.sendCommand("ON")
    
    sendPhoto()
    
    if switchOnTs == 0: relayServer.sendCommand("OFF")

def switchOn(source):
    global relayPin
    global switchOnTs
    
    #if source == Source.MOTION and switchOnTs > 0 : return

    relayServer.sendCommand("ON")
    switchOnTs = currentTime()

    if source == Source.MANUAL:
        sendPhoto()
    elif source == Source.MOTION:
        sendVideo()

def switchOff():
    global telegram
    global switchOnTs

    relayServer.sendCommand("OFF")
    switchOnTs = 0
    telegram.sendMessage("OFF")

def shouldTurnSwitchOff():
    global switchOnTs

    return switchOnTs > 0 and currentTime() - switchOnTs > 10 * 60


if __name__ == "__main__":
    switchOnTs = 0

    PIRPin = 4
    motionSensor = motionSensor.MotionSensor(PIRPin)

    relayServer = relayServer.RelayServer()
    relayServer.start()

    telegram = telegram.Telegram(config.telegramURL, config.telegramToken, config.telegramChatId)

    msgCnt = 0
    while True:
        if msgCnt == 10:
            msgCnt = 0
            msgs = telegram.getMessages()

            for msg in msgs:
                if msg.upper() == "ON":
                    print("ON")
                    switchOn(Source.MANUAL)

                elif msg.upper() == "OFF":
                    print("OFF")
                    switchOff()

                elif msg.upper() == "PHOTO":
                    print("PHOTO")
                    takePhoto()

                elif msg.upper() == "MOFF":
                    print("MOFF")
                    motionSensor.disable()
                    telegram.sendMessage("Done")

                elif msg.upper() == "MON":
                    print("MON")
                    motionSensor.enable()
                    telegram.sendMessage("Done")
        else:
            msgCnt += 1

        if motionSensor.triggered():
            print("Hareket")
            switchOn(Source.MOTION)

        if shouldTurnSwitchOff():
            print("OFF")
            switchOff()

        time.sleep(0.1)

