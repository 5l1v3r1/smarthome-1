#!/usr/bin/python3

import requests
import os
import time

import config

import motionSensor
import relayServer


class Source:
    MOTION = 0
    MANUAL = 1



    
def currentTime():
    return int(time.time())

def sendMessage(msg):

    try:
        r = requests.get("{0}{1}/sendMessage?chat_id={2}&text={3}".format(config.telegramURL, config.telegramToken, config.telegramChatId, msg))
    except:
        pass

def getMessages():
    global lastMessageTs
    global lastUpdateId

    msgs = []

    try:
        r = requests.get("{0}{1}/getUpdates?chat_id={2}&offset={3}".format(config.telegramURL, config.telegramToken, config.telegramChatId, lastUpdateId))

        updates = r.json()
    
        results = updates["result"]
    except:
        return msgs

    for update in results:
        lastUpdateId = update["update_id"]
        if update["message"]["date"] > lastMessageTs and 'text' in update["message"]:
            msgs.append(update["message"]["text"])
            lastMessageTs = update["message"]["date"]

    return msgs

def sendPhoto():
    os.system("fswebcam -r 640x480 --jpeg 85 -D 1 shot.jpg")

    f = open("shot.jpg", "rb")

    try:
        r = requests.post("{0}{1}/sendPhoto".format(config.telegramURL, config.telegramToken), data={"chat_id":config.telegramChatId}, files={"photo":f})
    except:
        pass
    f.close()

    os.remove("shot.jpg")
    
    
def sendVideo():
    os.system(" ffmpeg -t 10 -f v4l2 -framerate 25 -video_size 640x80 -i /dev/video0 video.mkv")

    f = open("video.mkv", "rb")
    
    try:
        r = requests.post("{0}{1}/sendVideo".format(config.telegramURL, config.telegramToken), data={"chat_id":config.telegramChatId}, files={"video":f})
    except:
        pass

    f.close()

    os.remove("video.mkv")
    
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
    global relayPin
    global switchOnTs

    relayServer.sendCommand("OFF")
    switchOnTs = 0
    sendMessage("OFF")

def shouldTurnSwitchOff():
    global switchOnTs

    return switchOnTs > 0 and currentTime() - switchOnTs > 10 * 60


if __name__ == "__main__":
    switchOnTs = 0

    lastMessageTs = currentTime()
    lastUpdateId = 0

    PIRPin = 4
    motionSensor = motionSensor.MotionSensor(PIRPin)

    relayServer = relayServer.RelayServer()
    relayServer.start()

    msgCnt = 0
    while True:
        if msgCnt == 10:
            msgCnt = 0
            msgs = getMessages()

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
                    motionSensorEnabled = False
                    sendMessage("Done")

                elif msg.upper() == "MON":
                    print("MON")
                    motionSensorEnabled = True
                    sendMessage("Done")
        else:
            msgCnt += 1

        if motionSensor.triggered():
            print("Hareket")
            switchOn(Source.MOTION)

        if shouldTurnSwitchOff():
            print("OFF")
            switchOff()

        time.sleep(0.1)

