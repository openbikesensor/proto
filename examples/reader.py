import logging

from obs.proto import read_serial

log = logging.getLogger(__name__)

distances = [0, 0]

for event in read_serial("/dev/ttyUSB0"):
    if event.HasField("distance_measurement"):
        d = event.distance_measurement
        if d.distance < 5:
            distances[d.source_id - 1] = d.distance
        print("  ".join(f"{dist*100:4.0f}cm" for dist in distances), end="\r")

    if event.HasField("text_message"):
        print(f"[Message] {event.text_message.text}")
