# FF20 protocol notes

## HID interfaces

| Interface | Purpose | Report size |
|---:|---|---:|
| 0 | Commands, status replies | 64 |
| 1 | Audio/data transfer | 1024 |

## Packet framing

```text
AA 55
Length uint16 little-endian
Command byte
Payload
CRC16
```

The CRC is calculated over:

```text
Length uint16 little-endian + Command + Payload
```

## Validated commands

| Command | Description |
|---:|---|
| `0x00` | Get version/device information |
| `0x82` | Read loop page |
| `0x84` | Upload/import audio |
| `0x86` | Query free space |
| `0x88` | Delete loop |

## Loop read payload

Command: `0x82`

```text
index uint16 little-endian
page uint32 little-endian
```

Page `0` returns metadata. Pages `1..n` return audio data.

## Audio format

Device storage format:

```text
44100 Hz
Stereo
Signed 24-bit little-endian PCM
6 bytes per stereo frame
```

Vendor export pads each 24-bit sample to 32-bit PCM as:

```text
00 b0 b1 b2
```
