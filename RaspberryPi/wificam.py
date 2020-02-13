import threading
import time
import socket

class WifiCam(threading.Thread):

    PING_CMD  = b'\x20'
    PONG_CMD  = b'\x21'
    PHOTO_CMD = b'\x22'
    VIDEO_CMD = b'\x23'


    def __init__(self):
        threading.Thread.__init__(self)

        self._cmdQueue = []
        self._photoQueue = []

    def run(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 42025))
            s.listen()
            while True:
                conn, addr = s.accept()
                print("New connection: ", addr)
                conn.settimeout(0.1)
                with conn:
                    while True:
                        if len(self._cmdQueue) == 0:
                            try:
                                cmd = conn.recv(1)


                            except socket.timeout:
                                continue
                            except:
                                print("Connection closed")
                                break

                            if cmd == WifiCam.PING_CMD:
                                conn.sendall(WifiCam.PONG_CMD)
                            elif cmd == WifiCam.PHOTO_CMD:
                                conn.settimeout(0)
                                data = conn.recv(4)
                                while len(data) < 4:
                                    data += conn.recv(4 - len(data))

                                pLen = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

                                data = conn.recv(pLen)
                                while len(data) < pLen:
                                    data += conn.recv(pLen - len(data))

                                conn.settimeout(0.1)
                                self._photoQueue.append(data)

                            continue

                        cmd = self._cmdQueue.pop()
                        try:
                            conn.sendall(cmd)
                        except:
                            self._cmdQueue.insert(0, cmd)
                            break

                    conn.close()
                    time.sleep(0.1)

    def sendCommand(self, cmd):
        self._cmdQueue.append(cmd)

    def takePhoto(self):
        self.sendCommand(WifiCam.PHOTO_CMD)

        while True:
            if len(self._photoQueue) == 0:
                time.sleep(0.1)
                continue

            return self._photoQueue.pop()



