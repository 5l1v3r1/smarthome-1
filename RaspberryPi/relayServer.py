import threading
import socket


class RelayServer(threading.Thread):

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

            conn.settimeout(0.1)

            while True:
                if len(self._cmdQueue) == 0:
                    try:
                        data = conn.recv(256)
                        while len(data) < 5:
                            data += conn.recv(256)

                        if "PING" in data.decode("ascii"):
                            conn.sendall("PONG\n".encode("ascii"))
                    except socket.timeout:
                        pass
                    except:
                        print("[+] Connection to relay server is closed.")
                        break

                    continue

                cmd = self._cmdQueue.pop()
                try:
                    conn.sendall("{0}\n".format(cmd).encode("ascii"))
                except:
                    self._cmdQueue.insert(0, cmd)
                    break

            conn.close()

    def sendCommand(self, cmd):
        self._cmdQueue.append(cmd)