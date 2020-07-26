import threading
import socket


class RelayServer(threading.Thread):

    PING_CMD = b'\x20'
    PONG_CMD = b'\x21'
    ON_CMD   = b'\x25'
    OFF_CMD  = b'\x26'


    def __init__(self):
        threading.Thread.__init__(self)

        self._cmdQueue = []

    def run(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        s.bind(("0.0.0.0", 42024))
        s.listen()

        while True:
            conn, addr = s.accept()
            print("[+] New connection to relay server from {0}.".format(addr))

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
                        conn.sendall(RelayServer.PING_CMD)
                    except:
                        print("[+] Connection to WifiCam server is closed.")
                        break

                try:
                    data = conn.recv(1)

                    if data == RelayServer.PING_CMD:
                        conn.sendall(RelayServer.PONG_CMD)
                except socket.timeout:
                    pass
                except:
                    print("[+] Connection to relay server is closed.")
                    break

            conn.close()

    def sendCommand(self, cmd):
        self._cmdQueue.append(cmd)
