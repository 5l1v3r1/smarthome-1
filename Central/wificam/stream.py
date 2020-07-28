import http.server
import random
import socket
import string
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler

class CamPipe(threading.Thread):

        def run(self):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            s.bind(("0.0.0.0", 42026))
            s.listen()

            while True:
                self._conn, addr = s.accept()
                print("[+] New connection to proxy server from {0}.".format(addr))

        def recv(self, n):
            try:
                return self._conn.recv(n)
            except:
                return b""

        def stopStream(self):
            self._conn.close()

def CreateHandler(wificam, pipe):
    class StreamServerHandler(http.server.BaseHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            self.pipe = pipe
            self.wificam = wificam

            super(StreamServerHandler, self).__init__(*args, **kwargs)

        def do_GET(self):
            if self.path != "/homestream":
                self.send_response(404)
                self.end_headers()
                return

            boundary = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace;boundary={0}".format(boundary))
            self.end_headers()

            self.wificam.stream()

            while True:
                data = self.pipe.recv(4)
                while len(data) < 4:
                    data += self.pipe.recv(4 - len(data))

                pLen = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

                if pLen == 0:
                    self.pipe.stopStream()
                    return

                data = self.pipe.recv(pLen)
                while len(data) < pLen:
                    data += self.pipe.recv(pLen - len(data))

                chunk = data

                try:
                    self.wfile.write(b"--" + boundary.encode("ascii")
                                     + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(pLen).encode("ascii") + b"\r\n\r\n")

                    self.wfile.write(chunk)

                    self.wfile.write(b"\r\n")
                except:
                    self.pipe.stopStream()
                    return

    return StreamServerHandler

class StreamServer(threading.Thread):

    def __init__(self, wificam):
        self._pipe = CamPipe()
        self._httpd = http.server.HTTPServer(("0.0.0.0", 8080), CreateHandler(wificam, self._pipe))

        threading.Thread.__init__(self)

    def run(self):
        self._pipe.start()
        self._httpd.serve_forever()
