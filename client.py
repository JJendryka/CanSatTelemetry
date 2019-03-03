from threading import Thread
import socket
import queue
import serial
from datetime import datetime


class Client(Thread):
    def __init__(self, data_queue, port, baud):
        Thread.__init__(self)
        self.data_queue = data_queue
        self.port = port
        self.baud = baud

    def run(self):
        while True:
            try:
                with serial.Serial(port=self.port, baudrate=self.baud) as ser:
                    with open("logs/" + self.port.split("/")[-1] + "-" + str(datetime.now()), "wb") as f:
                        while True:
                            data = ser.read()
                            f.write(data)
                            for b in data:
                                self.data_queue.put(b)
            except serial.SerialException:
                print(self.port + " disconnected")
                pass
