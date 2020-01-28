import time

import requests


class Telegram:

    def __init__(self, url, token, chatId):
        self._chatId = chatId
        self._token = token
        self._url = url

        self._lastMessageTs = int(time.time())
        self._lastUpdateId = 0

    def getMessages(self):
        msgs = []

        try:
            r = requests.get("{0}{1}/getUpdates?chat_id={2}&offset={3}".format(self._url, self._token,
                                                                               self._chatId, self._lastUpdateId))

            updates = r.json()

            results = updates["result"]
        except:
            return msgs

        for update in results:
            self._lastUpdateId = update["update_id"]
            if update["message"]["date"] > self._lastMessageTs and 'text' in update["message"]:
                msgs.append(update["message"]["text"].upper())
                self._lastMessageTs = update["message"]["date"]

        return msgs

    def sendMessage(self, msg):
        try:
            requests.get("{0}{1}/sendMessage?chat_id={2}&text={3}".format(self._url, self._token, self._chatId, msg))
        except:
            pass

    def sendVideo(self, videoFd):
        try:
            requests.post("{0}{1}/sendVideo".format(self._url, self._token),
                              data={"chat_id": self._chatId}, files={"video": videoFd})
        except:
            pass

    def sendPhoto(self, photoFd):
        try:
            requests.post("{0}{1}/sendPhoto".format(self._url, self._token),
                              data={"chat_id": self._chatId}, files={"photo": photoFd})
        except:
            pass
