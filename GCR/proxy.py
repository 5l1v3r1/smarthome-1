#!/usr/bin/env python3
import random
import socket
import string

from http.server import HTTPServer, BaseHTTPRequestHandler

class Streamer(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        s.bind(("0.0.0.0", 42026))
        s.listen()

        self.s = s
        super(Streamer, self).__init__(*args, **kwargs)

    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        boundary = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace;boundary={0}".format(boundary))
        self.end_headers()

        conn, addr = self.s.accept()
        print("[+] New connection to proxy server from {0}.".format(addr))

        # conn.settimeout(0.1)
        with conn:
            while True:
                data = conn.recv(4)
                while len(data) < 4:
                    data += conn.recv(4 - len(data))

                pLen = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

                if pLen == 0:
                    conn.close()
                    return

                data = conn.recv(pLen)
                while len(data) < pLen:
                    data += conn.recv(pLen - len(data))

                chunk = data

                try:
                    self.wfile.write(b"--" + boundary.encode("ascii")
                                     + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(pLen).encode("ascii") + b"\r\n\r\n")

                    self.wfile.write(chunk)

                    self.wfile.write(b"\r\n")
                except:
                    conn.close()
                    return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 8000), Streamer)
    httpd.serve_forever()
