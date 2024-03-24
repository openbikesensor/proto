import argparse
from datetime import datetime
import logging

from cobs import cobs
import pandas

from obs.proto import Event, Time

log = logging.getLogger(__name__)


def parse_event(data: bytes):
    event = Event()
    event.ParseFromString(data)
    return event


distances = [0, 0]

NULL = b"\x00"


def read_chunks(f):
    buf = []
    while True:
        byte = f.read(1)
        if byte == NULL:
            yield b"".join(buf)
            buf = []
        elif byte == b"":
            return
        else:
            buf.append(byte)


def main():
    parser = argparse.ArgumentParser(
        description="Convert OpenBikeSensor recording binary to tabular format for easier parsing or manual usage."
    )
    parser.add_argument("input", type=argparse.FileType("rb"))
    parser.add_argument("output", type=argparse.FileType("wt"))
    args = parser.parse_args()

    df = []
    headers = [
        "Event type",
        "OBS Time",
        "Phone time",
        "Latitude",
        "Longitude",
        "Left",
        "Right",
        "Message",
    ]

    for chunk in read_chunks(args.input):
        try:
            packet = cobs.decode(chunk)
        except Exception:
            log.exception("Failed to decode COBS packet, skipping message")
            continue

        try:
            event = parse_event(packet)
        except Exception:
            log.exception("Failed to parse Event packet, skipping message")
            continue

        event_type = event.WhichOneof("content")
        row = [event_type]

        time_by_source_id = {}
        for time in event.time:
            try:
                source_id = time.source_id
            except ValueError:
                source_id = 0
            time_by_source_id[source_id] = time

        for source_id in (0, 2):
            time = time_by_source_id.get(source_id)
            if time is None:
                row.append(None)
                continue

            seconds = time.seconds + (time.nanoseconds * 1e-9)

            if time.reference == Time.UNIX:
                dt = datetime.fromtimestamp(seconds)
                row.append(dt.isoformat())
            else:
                row.append(time.seconds + (time.nanoseconds * 1e-9))

        if event.HasField("geolocation"):
            row.append(event.geolocation.latitude)
            row.append(event.geolocation.longitude)
        else:
            row.append(None)
            row.append(None)

        if event.HasField("distance_measurement"):
            d = event.distance_measurement
            dist = None if d.distance > 5 else d.distance
            if d.source_id == 1:
                row.append(dist)
                row.append(None)
            elif d.source_id == 2:
                row.append(None)
                row.append(dist)
            else:
                row.append(None)
                row.append(None)
        else:
            row.append(None)
            row.append(None)

        if event.HasField("text_message"):
            row.append(event.text_message.text)

        df.append(row)

    df = pandas.DataFrame(df)
    try:
        df.to_csv(args.output, header=headers, index=False, sep=";")
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
