import serial
from cobs import cobs

from .openbikesensor_pb2 import Event


def parse_event(data: bytes):
    event = Event()
    event.ParseFromString(data)
    return event


distances = [0, 0]

NULL = b"\x00"


def read_serial(port="/dev/ttyUSB0", baud=115200):
    with serial.Serial(port, baud) as ser:
        while True:
            chunk = ser.read_until(expected=NULL)[:-1]

            if NULL in chunk:
                continue  # found incomplete chunk

            try:
                packet = cobs.decode(chunk)
            except Exception as e:
                # log.exception("Failed to decode COBS packet, skipping message")
                continue

            try:
                event = parse_event(packet)
            except Exception as e:
                # log.exception("Failed to parse Event packet, skipping message")
                continue

            yield event
