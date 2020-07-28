import os
import threading
import time
import socket
import subprocess
import wificam.stream

class WifiCam(threading.Thread):

    PING_CMD   = b'\x20'
    PONG_CMD   = b'\x21'
    PHOTO_CMD  = b'\x22'
    VIDEO_CMD  = b'\x23'
    STREAM_CMD = b'\x24'
    MON_CMD    = b'\x27'
    MOFF_CMD   = b'\x28'


    def __init__(self, telegram):
        threading.Thread.__init__(self)

        self._telegram = telegram

        self._cmdQueue = []
        self._photoQueue = []
        self._frameQueue = []

        self._httpd = wificam.stream.StreamServer(self)

    def run(self):
        # self._httpd.start()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        s.bind(("0.0.0.0", 42025))
        s.listen()

        while True:
            conn, addr = s.accept()
            print("[+] New connection to WifiCam server from {0}.".format(addr))

            conn.settimeout(0.5)

            while True:
                if len(self._cmdQueue) > 0:
                    cmd = self._cmdQueue.pop()
                    try:
                        conn.sendall(cmd)
                    except:
                        self._cmdQueue.insert(0, cmd)
                        break

                    continue
                else: # check if connection is alive
                    try:
                        conn.sendall(WifiCam.PING_CMD)
                    except:
                        print("[+] Connection to WifiCam server is closed.")
                        break

                cmd = b''
                try:
                    cmd = conn.recv(1)

                except socket.timeout:
                    continue

                except:
                    print("[+] Connection to WifiCam server is closed.")
                    break

                try:
                    if cmd == WifiCam.PING_CMD:
                        conn.sendall(WifiCam.PONG_CMD)
                    elif cmd == WifiCam.PHOTO_CMD:
                        conn.settimeout(None)

                        data = conn.recv(4)
                        while len(data) < 4:
                            data += conn.recv(4 - len(data))

                        pLen = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

                        data = conn.recv(pLen)
                        while len(data) < pLen:
                            data += conn.recv(pLen - len(data))

                        conn.settimeout(0.5)

                        self._telegram.sendPhoto(data)
                    elif cmd == WifiCam.VIDEO_CMD:
                        conn.settimeout(None)

                        while True:
                            data = conn.recv(4)
                            while len(data) < 4:
                                data += conn.recv(4 - len(data))

                            pLen = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

                            if pLen == 0:
                                break

                            data = conn.recv(pLen)
                            while len(data) < pLen:
                                data += conn.recv(pLen - len(data))

                            self._frameQueue.append(data)

                        self._frameQueue.append("END")

                        conn.settimeout(0.5)

                except:
                    print("[+] Connection to WifiCam server is closed.")
                    break

            conn.close()
            time.sleep(0.1)

    def sendCommand(self, cmd):
        self._cmdQueue.append(cmd)

    def takePhoto(self):
        self.sendCommand(WifiCam.PHOTO_CMD)

    def record(self):
        self.sendCommand(WifiCam.VIDEO_CMD)

        frameId = 0
        startTime = time.time()
        convStarted = False
        while True:
            if len(self._frameQueue) == 0:
                time.sleep(0.1)
                continue

            frame = self._frameQueue.pop()

            if frame == "END":
                break

            f = open("frames/frame{0:04d}.jpg".format(frameId), "wb")
            f.write(frame)
            f.close()

            frameId+=1

            if frameId == 15:
                totalTime = time.time() - startTime
                rate = 15 / totalTime

                if rate < 3:
                    print("here")
                    os.system(
                        "ffmpeg -y -r {0} -t 9 -i frames/frame%04d.jpg -c:v mpeg4 -vf scale=320x240 frames/video.mp4 &".format(int(rate)))
                    convStarted = True


            if frameId == 25 and not convStarted:
                print("here")
                os.system("ffmpeg -y -r 5 -t 9 -i frames/frame%04d.jpg -c:v mpeg4 -vf scale=320x240 frames/video.mp4 &")
                convStarted = True

        print("id:", frameId)
        if convStarted:
            while True:
                process = subprocess.Popen("ps aux | grep ffmpeg | grep -v grep", shell=True, stdout=subprocess.PIPE)
                result = process.communicate()[0]

                if result.strip() == b"": break

                time.sleep(0.2)
        else:
            os.system("ffmpeg -y -r 5 -t 9 -i frames/frame%04d.jpg -c:v mpeg4 -vf scale=320x240 frames/video.mp4")

        f = open("frames/video.mp4", "rb")
        video = f.read()
        f.close()

        for i in range(frameId):
            os.remove("frames/frame{0:04d}.jpg".format(i))

        os.remove("frames/video.mp4")

        return video

    def stream(self):
        self.sendCommand(WifiCam.STREAM_CMD)

    def sensorOn(self):
        self.sendCommand(WifiCam.MON_CMD)

    def sensorOff(self):
        self.sendCommand(WifiCam.MOFF_CMD)
