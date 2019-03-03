from pprint import pprint
from threading import Thread
import queue
import struct
import crc8
import json
import math

START = 0x01


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

        self.calibrationNTC = {'R_0':33000, 'T_0':298.15, 'R_1': 33000, 'B':5000, 'resolution':12}
        self.calibrationVBAT = {'multiplier':0.5, 'refrence':2.50}

        self.parse(data)

    def parse(self, data):
        raw_temp1, raw_temp2, self.temp3, self.temp4, raw_pressure, self.timestamp, raw_vbat, self.humid, self.checksum = struct.unpack(
            'xxhhhhhIhBB', bytearray(data))
        self.pressure = self.convert_pressure(raw_pressure)
        self.temp1 = self.convertNTC(raw_temp1, **self.calibrationNTC)
        self.temp2 = self.convertNTC(raw_temp2, **self.calibrationNTC)
        self.vbat = self.convertVBAT(raw_vbat, **self.calibrationVBAT)

    def convert_pressure(self, pressureRaw):
        return (pressureRaw / 100.0) + 750.0

    def convertNTC(self, temperature_raw, R_1, resolution, T_0, B, R_0):
        R = R_1 * ((2**resolution) / temperature_raw - 1)
        T = 1/(1/T_0 + 1/B * math.log(R/R_0))
        return T - 273.18

    def convert_vbat(self, vbat_raw, multiplier, reference):
        return vbat_raw * multiplier * reference



class GPSPack(Pack):
    def __init__(self, data):
        Pack.__init__(self)
        self.type = "GPS"
        self.hdop = None
        self.hour = None
        self.minute = None
        self.seconds = None
        self.lat = None
        self.lon = None
        self.height = None
        self.parse(data)

    def parse(self, data):
        rawHDOP, self.timestamp, rawGPStime, self.lat, self.lon, self.height, self.checksum = struct.unpack(
            "xxBxIIfffB", bytearray(data))
        self.hdop = self.convertHDOP(rawHDOP)
        self.hour, self.minute, self.second = self.convertGPStime(rawGPStime)

    def convertHDOP(self, rawHDOP):
        return rawHDOP / 10.0

    def convertGPStime(self, rawGPStime):
        text = str(rawGPStime)
        hour = int(text[:2])
        minute = int(text[2:4])
        second = int(text[4:6])
        return [hour, minute, second]

        


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
