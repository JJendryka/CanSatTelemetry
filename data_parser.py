from queue import Queue
import client
import server
import parsing
import httpserver
import threading
from threading import Thread
from pprint import pprint


def start():
    packet_queue = Queue()
    relay_queue = Queue()
    server_thread = server.Server(packet_queue)
    http_thread = httpserver.HTTPServer(packet_queue)
    http_thread.start()
    server_thread.start()
    connect_device('/dev/ttyACM1', 9600, packet_queue,
                   server_thread.broadcast, relay_queue, False)
    connect_device('/dev/ttyACM0', 115200, packet_queue,
                   server_thread.broadcast, relay_queue, True)

    while threading.active_count() > 0:
        pass


def connect_device(port, baud, packet_queue, broadcast, relay_queue, relay):
    parsing_queue = Queue()
    if relay:
        client_thread = client.Client(parsing_queue, port, baud, relay_queue)
    else:
        client_thread = client.Client(parsing_queue, port, baud)
    parser_thread = parsing.Parser(
        parsing_queue, packet_queue, broadcast, relay_queue)
    client_thread.start()
    parser_thread.start()


if __name__ == "__main__":
    start()
