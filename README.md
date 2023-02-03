# OpenBikeSensor Recording Format

⚠️🚧 The contents of this repository are current a draft. Don't use this for important projects yet, as things might still change, and quickly.

This repository contains the files and definitions necessary to work with **binary** recordings created by and for OpenBikeSensor devices, software and compatible projects.

🔍 Looking for the **CSV** Format description? This is not it, [look here instead](https://github.com/openbikesensor/OpenBikeSensorFirmware/blob/master/docs/software/firmware/csv_format.md).

## Quick start

* Want to use protocol buffers in your project directly? 
  - Compile and import [`openbikesensor.proto`](./openbikesensor.proto). Check
    [protobuf.dev](https://protobuf.dev/) on how to do that in your language.
* Want to parse and write files from python? 
  - Install this repository as a package (`make install-dev` or `make install`)
    into your python environment. 
  - Use `from obs.proto import Event, UserInput` etc and use like any protocol
    buffer generated code (see protobuf docs).
  - Or use `from obs.proto import read_serial`. It will open a serial port and
    iterate over instances of `Event` for you.


## Design goals

* **Message based**: A single message contains structured information that represent real-world happenings, and those messages are generated as their events happen in real-time.
* **Streamable**: Separate messages can be sent or stored and possibly interpreted independently from one another, without becoming unusable. A recording can be created by storing these messages as they appear, without the need to fully buffer the whole contents.
* **Time referenced**: Messages must be referenced in time, but different systems do not need to share a synchronized time reference. Synchronization may be defered to a later point in time, when more information about the relation between different time references is available.
* **Mergeable and filterable**: Messages from different sources shall easily be combinable into a single stream. The evaluation process is enabled to join information from multiple sources and logically group them into different subsets, then treat those separately again. An intermediate device or software shall be able to filter out certain messages that are deemed irrelevant for the downstream receivers.
* **Extensible**: The format of each message must be extensible independently. Messages that cannot be interpreted by a receiver must be skippable. The format shall be future-proof.
* **Compact**: The data format shall be as compact as possible to save storage, bandwidth and memory. This is especially important for use with embedded and mobile devices.
* **Well documented**: TBD
* **Convertible**: A recording in this format should be convertible to a format that can easily be edited by a human being, such as a text or tabular format.


## General idea

This specification primarily deals with the format of a single message. Each message has its own atomic meaning and can (most of the time) be interpreted without referencing other messages.

Messages are encoded based on the transmission protocol. When using a protocol that is already package-based (with packages of arbitrary size), no additional mechanism is required to separate messages in transmission. In serial streams of data or when stored in files, an additional message separation technique is required. This depends on the format and underlying transport protocol and is specified below, if available. The actual message contents are the same regardless of the transport used.


## Serial protocol

The serial protocol is used when a simple embedded device (such as the OpenBikeSensor Lite) transmits message on a serial interface that does not support message separation on its own.

Message separation is achieved using [COBS](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing). This is implemented in devices based on the Arduino platform using the [PacketSerial](https://www.arduino.cc/reference/en/libraries/packetserial/) library. Equivalent implementations can be used on any other platform.


## File storage

A file containing messages with this format shall have the extension `.obsr` (OpenBikeSensor Recording) and contain messages encoded into messages using [COBS](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing). This makes these files easy to produce as a stream by appending data as it becomes available.

The file may optionally be compressed further using `gzip`, in which case the extension `.obsp.gz` should be used. Consumers of files should try to auto-detect the usage of compression and also allow `.obsp` files (or a file of any ending for that matter) to be either a compressed or an uncompressed COBS stream.


## Message Semantics

The protocol buffer format specifies the `Event` message type, which is the root entry for each message on this format. An event usually has one or more timestamps attached to it (see below), and a content of one of the specified subtypes.


### Time

Within one stream or recording, different events may be referenced to different sources of time. Such a time source may be an internal clock of a microprocessor device, a real-time clock, or even network or GPS time.

Each time source is assigned a unique ID per stream or recording, so multiple events can be related to each other temporally if they reference the same time source. A single event may also be referenced to multiple time sources, which provides a way to synchronize these sources during analysis. If multiple sources are in conflict, the more accurate reference should be chosen (generally, GPS is more accurate than most UTC-based times, and arbitrary references, such as microcontroller clocks, are least accurate). Synchronization may also occur at different points in time (when available), in which case the less accurate time source can be corrected through interpolation from the more accurate time source.

Time entries are given as seconds and nanoseconds. The seconds part can be negative or positive. The nanoseconds part must be in the range 0 to 999999999 (inclusive) and must always count forward in time from the seconds entry (so -0.5 seconds before the reference time is encoded as -1 second and 500000000 nanoseconds).


### DistanceMeasurement 

A measurement done with a distance sensor is recorded as a DistanceMeasurement entry. Each message contains only one measurement. The sensor is assigned a source ID by the recording device, the mapping to a sensor position (such as left or right) is done by convention, by the device specification, or further specified in the metadata (see below).

The measurement is provided as a distance in meters. A quality can be assigned that describes a relative measure of the certainty of the device that the measurement is accurate. This quality value should be between 0 and 1, a value of 0 shall be interpreted as a missing quality information.

The measurement, if done by a time-of-flight sensor, can also specify the TOF duration of the signal in picoseconds. It is assumed that the medium (sound or light) can be inferred from the relation between this value and the provided distance value, or the absolute size of the TOF value alone. During analysis, additional information (such as ambient temperature) can improve the result of the distance calculation from this value which might not be available to the device when the event was emitted. The analysis may therefore chose to ignore the provided distance and recompute the distance from the TOF value instead.


### TextMessage

The device may send text messages to assist in debugging or provide other human-readable information. A text message has a type to help flag understand its urgency or nature.


### UserInput

This event is used to signal when a user has interacted with the device to mark a location or situation in the recording. 

The meaning of the interaction is decided by the button mapping of the device and should be communicated to the user. There are various event types for marking different situations. 

The event can either mark the very instant something happened (`timing=IMMEDIATE`) or whether the situation started or ended (`timing=START` and `END`, respectively). Depending on the type of input, `timing=IMMEDIATE` can also signal a toggling of a state, such as the pause state or private mode. 

If the recording device is aware of the relative direction (e. g. because its inputs have been configured accordingly) of the cause of the interaction, it can signal this through the `direction` field. 

Finally, addons can use the `addon` field to use arbitrary unique identifiers additional types of interaction that are not mapped. 

An example event for an "overtaking" as confirmed by a standard OpenBikeSensor might be recorded as: `UserInput {type=OVERTAKER, direction=LEFT, timing=IMMEDIATE}`. A different survey might add two custom buttons to the device that send start/end markers for dooring zones on the right of the bicycle that look like this: `UserInput {type=DOORING_ZONE, direction=RIGHT, timing=START}` and also with `timing=END`.

### Geolocation

The location of the device is encoded with this message type. Each source of location information is assigned a unique ID per stream or recording. Latitude and longitude should be provided, based on WSG84 as the reference coordinate system. They are given in degrees of latitude (north positive, south negative) in range -90 to 90 and degrees of longitude (east positive, west negative) in range -180 to 180.

If available, an altitude in meters above mean sea level can be provided.

The ground speed (meters per second) and true heading (degrees clockwise from north), number of visible/used satellites, HDOP value and signal to noise ratio (in decibels?) can also be provided for debugging or analysis.


### Metadata

The following entries are used in the OpenBikeSensor devices:

- `SensorPosition1=left`, the placement of the sensor with `source_id=1`. One of `left` or `right`.
- `SensorPosition2=right`, see above.
