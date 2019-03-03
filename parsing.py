from pprint import pprint
from threading import Thread
import queue
import struct
import crc8
import json

START = 1


class ChecksumException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class Parser(Thread):
    def __init__(self, data_queue, packet_queue, broadcast):
        Thread.__init__(self)
        self.data_queue = data_queue
        self.packet_queue = packet_queue
        self.broadcast = broadcast

    def run(self):
        while True:
            if self.data_queue.qsize() >= 2:
                if self.data_queue.queue[0] == START:
                    if self.data_queue.queue[1] in type_dict:
                        constructor, length = type_dict[self.data_queue.queue[1]]
                        while self.data_queue.qsize() < length:
                            pass
                        try:
                            packet = constructor(
                                list(self.data_queue.queue)[:length])
                            print("Packet found: ", packet.__class__.__name__)
                            self.packet_queue.put(packet)
                            self.broadcast(json.dumps(packet.__dict__))
                        except ChecksumException:
                            print("Checksum failed")
                self.data_queue.get()


class Pack:

    def __init__(self):
        self.type = None
        self.timestamp = None
        self.checksum = None

    def show(self):
        pprint(vars(self))

    def validate(self, data):
        if crc8.crc8((bytearray(data)[:len(bytearray(data))-2])) != self.checksum:
            raise ChecksumException


class TemperaturePack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "TEMP"
        self.temp1 = None
        self.temp2 = None
        self.temp3 = None
        self.temp4 = None
        self.pressure = None
        self.vbat = None
        self.humid = None
        self.checksum = None
        self.parse(data)

    def parse(self, data):
        self.temp1, self.temp2, self.temp3, self.temp4, self.pressure, self.timestamp, self.vbat, self.humid, self.checksum = struct.unpack(
            'xxhhhhhIhBB', bytearray(data))


class GPSPack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "GSP"
        self.hdop = None
        self.gpstime = None
        self.lat = None
        self.lon = None
        self.height = None
        self.parse(data)

    def parse(self, data):
        self.hdop, self.timestamp, self.gpstime, self.lat, self.lon, self.height, self.checksum = struct.unpack(
            "xxBxIIfffB", bytearray(data))


class AirPack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "AIR"
        self.millis = None
        self.deviation = None
        self.range = None
        self.parse(data)

    def parse(self, data):
        self.deviation, self.timestamp, self.millis, self.range, self.checksum = struct.unpack(
            "xxHIIHB", bytearray(data))


class AccPack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "ACC"
        self.accx = None
        self.accy = None
        self.accz = None
        self.gyrx = None
        self.gyry = None
        self.gyrz = None
        self.parse(data)

    def parse(self, data):
        self.accx, self.timestamp, self.accy, self.accz, self.gyrx, self.gyry, self.gyrz, self.checksum = struct.unpack(
            "xxhIhhhhhB", bytearray(data))


class RSSIPack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "RSSI"
        self.rssi = None
        self.parse(data)

    def parse(self, data):
        self.rssi, self.timestamp, self.checksum = struct.unpack(
            "xxhIB", bytearray(data))


type_dict = {
    2: (TemperaturePack, 20),
    3: (GPSPack, 25),
    4: (AirPack, 15),
    5: (AccPack, 19),
    6: (RSSIPack, 9),
}
