import http
from threading import Thread
from http.server import BaseHTTPRequestHandler
import json


class HTTPServer(Thread):
    def __init__(self, packet_queue):
        Thread.__init__(self)
        self.packet_queue = packet_queue

    def run(self):
        server_address = ("localhost", 8080)
        handlerClass = HTTPHandler
        handlerClass.queue = self.packet_queue
        httpd = http.server.HTTPServer(server_address, handlerClass)
        httpd.serve_forever()


class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_HEAD(self):
        return

    def do_GET(self):
        self.respond()

    def do_POST(self):
        return

    def handle_http(self, status, content_type):
        if self.path == "/":
            status = 200
            content_type = "text/html"
            response_content = open("index.html")
            response_content = response_content.read()
        elif self.path == "/data.json" or self.path == "/data":
            status = 200
            content_type = "text/json"
            packets = [packet.__dict__ for packet in self.queue.queue]
            response_content = json.dumps(packets)

        else:
            status = 404
            content_type = "text/plain"
            response_content = "404 Not Found"

        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()
        return bytes(response_content, "UTF-8")

    def respond(self):
        content = self.handle_http(200, "text/html")
        self.wfile.write(content)
