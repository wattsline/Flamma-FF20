from __future__ import annotations

import struct
from typing import Iterable, Optional, Sequence

CRC_TABLE = [
    0,4129,8258,12387,16516,20645,24774,28903,33032,37161,41290,45419,49548,53677,57806,61935,
    4657,528,12915,8786,21173,17044,29431,25302,37689,33560,45947,41818,54205,50076,62463,58334,
    9314,13379,1056,5121,25830,29895,17572,21637,42346,46411,34088,38153,58862,62927,50604,54669,
    13907,9842,5649,1584,30423,26358,22165,18100,46939,42874,38681,34616,63455,59390,55197,51132,
    18628,22757,26758,30887,2112,6241,10242,14371,51660,55789,59790,63919,35144,39273,43274,47403,
    23285,19156,31415,27286,6769,2640,14899,10770,56317,52188,64447,60318,39801,35672,47931,43802,
    27814,31879,19684,23749,11298,15363,3168,7233,60846,64911,52716,56781,44330,48395,36200,40265,
    32407,28342,24277,20212,15891,11826,7761,3696,65439,61374,57309,53244,48923,44858,40793,36728,
    37256,33193,45514,41451,53516,49453,61774,57711,4224,161,12482,8419,20484,16421,28742,24679,
    33721,37784,41979,46042,49981,54044,58239,62302,689,4752,8947,13010,16949,21012,25207,29270,
    46570,42443,38312,34185,62830,58703,54572,50445,13538,9411,5280,1153,29798,25671,21540,17413,
    42971,47098,34713,38840,59231,63358,50973,55100,9939,14066,1681,5808,26199,30326,17941,22068,
    55628,51565,63758,59695,39368,35305,47498,43435,22596,18533,30726,26663,6336,2273,14466,10403,
    52093,56156,60223,64286,35833,39896,43963,48026,19061,23124,27191,31254,2801,6864,10931,14994,
    64814,60687,56684,52557,48554,44427,40424,36297,31782,27655,23652,19525,15522,11395,7392,3265,
    61215,65342,53085,57212,44955,49082,36825,40952,28183,32310,20053,24180,11923,16050,3793,7920
]


def crc16(data: bytes | bytearray | Iterable[int]) -> bytes:
    crc = 0
    for b in data:
        crc = (CRC_TABLE[((crc >> 8) ^ b) & 0xFF] ^ ((crc << 8) & 0xFFFF)) & 0xFFFF
    crc ^= 0xFFFF
    return bytes([(crc >> 8) & 0xFF, crc & 0xFF])


def pack_command(cmd: int, payload: bytes | bytearray | Iterable[int] = b"") -> bytes:
    body = bytes([cmd]) + bytes(payload)
    framed = struct.pack("<H", len(body)) + body
    return bytes([0xAA, 0x55]) + framed + crc16(framed)


class ReplyParser:
    """Incremental parser for FF20 command-interface replies."""

    def __init__(self) -> None:
        self.buf = bytearray()

    def feed(self, report: Sequence[int] | bytes | bytearray) -> Optional[bytes]:
        data = bytes(report)
        if data:
            # The vendor app discards byte 0 from command HID reports.
            data = data[1:]

        self.buf.extend(data)

        while len(self.buf) >= 2 and not (self.buf[0] == 0xAA and self.buf[1] == 0x55):
            del self.buf[0]

        if len(self.buf) < 7:
            return None

        length = struct.unpack_from("<H", self.buf, 2)[0]
        total_len = 2 + 2 + length + 2
        if len(self.buf) < total_len:
            return None

        framed = bytes(self.buf[2:2 + 2 + length])
        got_crc = bytes(self.buf[2 + 2 + length:total_len])
        want_crc = crc16(framed)
        packet = bytes(self.buf[4:4 + length])
        del self.buf[:total_len]

        if got_crc != want_crc:
            raise IOError(f"CRC mismatch: got={got_crc.hex()} want={want_crc.hex()} packet={packet.hex()}")

        return packet
