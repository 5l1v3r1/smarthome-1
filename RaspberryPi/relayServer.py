import threading
import socket


class RelayServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self._cmdQueue = []

    def run(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            s.bind(("0.0.0.0", 42024))
            s.listen()
            while True:
                conn, addr = s.accept()
                print("New connection: ", addr)
                conn.settimeout(0.1)
                with conn:
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
                                print("Connection closed")
                                break
                            continue

                        cmd = self._cmdQueue.pop()
                        try:
                            conn.sendall((cmd + "\n").encode("ascii"))
                        except:
                            self._cmdQueue.insert(0, cmd)
                            break

                    conn.close()

    def sendCommand(self, cmd):
        self._cmdQueue.append(cmd)