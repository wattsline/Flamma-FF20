from __future__ import annotations

import json
import struct
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional

from .audio import expand_s24le_to_vendor_s32le, prepare_import_audio, write_vendor_style_wav_header
from .constants import (
    BYTES_PER_FRAME_24BIT_STEREO,
    CMD_DELETE_LOOP,
    CMD_GET_VERSION,
    CMD_QUERY_SPACE,
    CMD_READ_LOOP_PAGE,
    CMD_UPLOAD_AUDIO,
    DATA_REPORT_SIZE,
    MAX_IMPORT_BYTES,
    MAX_MINUTES,
    SAMPLE_RATE,
)
from .exceptions import InvalidSlotError
from .protocol import ReplyParser, pack_command
from .transport import HIDTransport


ProgressCallback = Callable[[int], None]


@dataclass
class DeviceInfo:
    serial: str
    product: str
    app_version: str
    boot_version: str
    hw_version: str
    version_flag: str


@dataclass
class LoopInfo:
    index: int
    status_flag: int
    export_flag: int
    data_length: int

    @property
    def minutes(self) -> float:
        return self.data_length / BYTES_PER_FRAME_24BIT_STEREO / SAMPLE_RATE / 60

    @property
    def present(self) -> bool:
        return self.data_length > 0


class FF20Pedal:
    def __init__(self, serial: Optional[str] = None, verbose: bool = False) -> None:
        self.transport = HIDTransport(serial=serial, verbose=verbose)
        self.parser = ReplyParser()

    @property
    def serial(self) -> str:
        return self.transport.serial or ""

    @staticmethod
    def devices() -> list[dict]:
        return HIDTransport.all_devices()

    def open(self) -> "FF20Pedal":
        self.transport.open()
        return self

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> "FF20Pedal":
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _validate_slot(self, index: int) -> None:
        if index < 0 or index > 99:
            raise InvalidSlotError(f"Slot {index} is invalid. Slot must be between 0 and 99.")

    def _read_cmd_packet(self, timeout_ms: int = 3000) -> bytes:
        while True:
            report = self.transport.read_command_report(timeout_ms)
            packet = self.parser.feed(report)
            if packet is not None:
                return packet

    def _write_command(self, cmd: int, payload: bytes = b"", expect_reply: bool = True) -> bytes:
        self.transport.write_command_bytes(pack_command(cmd, payload))
        if expect_reply:
            return self._read_cmd_packet()
        return b""

    def info(self) -> DeviceInfo:
        packet = self._write_command(CMD_GET_VERSION)
        data = packet[1:]
        return DeviceInfo(
            serial=self.serial,
            product=data[0:32].decode(errors="ignore").replace("\x00", ""),
            app_version=data[32:39].decode(errors="ignore").replace("\x00", ""),
            boot_version=data[39:46].decode(errors="ignore").replace("\x00", ""),
            hw_version=data[46:53].decode(errors="ignore").replace("\x00", ""),
            version_flag=data[53:54].decode(errors="ignore").replace("\x00", ""),
        )

    def get_loop_page(self, index: int, page: int) -> bytes:
        self._validate_slot(index)
        payload = struct.pack("<HI", index, page)
        self.transport.write_command_bytes(pack_command(CMD_READ_LOOP_PAGE, payload))
        return self.transport.read_data_report()

    def get_loop_info(self, index: int) -> LoopInfo:
        page0 = self.get_loop_page(index, 0)
        return LoopInfo(
            index=index,
            status_flag=page0[0],
            export_flag=page0[2],
            data_length=struct.unpack_from("<I", page0, 4)[0],
        )

    def list_loops(self, count: int = 100, progress: Optional[ProgressCallback] = None) -> list[LoopInfo]:
        count = max(1, min(100, count))
        loops = []
        for i in range(count):
            loops.append(self.get_loop_info(i))
            if progress:
                progress(int((i + 1) / count * 100))
        return loops

    def delete_loop(self, index: int) -> None:
        self._validate_slot(index)
        self.transport.write_command_bytes(pack_command(CMD_DELETE_LOOP, struct.pack("<H", index)))
        self._read_cmd_packet()

    def export_wav(self, index: int, output_path: Path, progress: Optional[ProgressCallback] = None) -> Path:
        self._validate_slot(index)
        output_path = Path(output_path)
        page0 = self.get_loop_page(index, 0)
        data_length = struct.unpack_from("<I", page0, 4)[0]
        if data_length <= 0:
            raise InvalidSlotError(f"Loop slot {index} appears empty")

        frame_count = (data_length + DATA_REPORT_SIZE - 1) // DATA_REPORT_SIZE + 1
        cache = b""

        with wave.open(str(output_path), "wb") as wf:
            write_vendor_style_wav_header(wf)

            for current_frame in range(frame_count):
                if current_frame == 0:
                    continue

                data = self.get_loop_page(index, current_frame)[:DATA_REPORT_SIZE]
                offset = current_frame * DATA_REPORT_SIZE - data_length
                if offset > 0:
                    data = data[:-offset]

                if cache:
                    data = cache + data

                expanded, cache = expand_s24le_to_vendor_s32le(data)
                wf.writeframesraw(expanded)

                if progress:
                    progress(min(100, int(current_frame / max(1, frame_count - 1) * 100)))

        return output_path

    def query_free_bytes(self) -> int:
        rep = self._write_command(CMD_QUERY_SPACE)
        if len(rep) < 5:
            raise RuntimeError(f"Short free-space reply: {rep.hex()}")
        remaining_minutes = MAX_MINUTES - struct.unpack_from("<I", rep, 1)[0]
        return int(remaining_minutes * 60 * SAMPLE_RATE * BYTES_PER_FRAME_24BIT_STEREO)

    def import_pcm24le_stereo(self, index: int, pcm_path: Path, progress: Optional[ProgressCallback] = None) -> LoopInfo:
        self._validate_slot(index)
        pcm_path = Path(pcm_path)
        file_size = pcm_path.stat().st_size
        read_size = min(MAX_IMPORT_BYTES, file_size)
        if read_size <= 0:
            raise RuntimeError("Input PCM file is empty")

        free_bytes = self.query_free_bytes()
        if read_size > free_bytes:
            raise RuntimeError(f"Not enough FF20 space. Need {read_size}, available {free_bytes}")

        total_frames = (read_size + DATA_REPORT_SIZE - 1) // DATA_REPORT_SIZE

        loop_index = struct.pack("<H", index)
        loop_page0 = struct.pack("<I", 0)
        loop_length = struct.pack("<I", read_size)

        self.transport.write_command_bytes(pack_command(CMD_UPLOAD_AUDIO, loop_index + loop_page0))
        rep = self._read_cmd_packet()
        if not rep or rep[0] != 0x85:
            raise RuntimeError(f"Import init failed: {rep.hex() if rep else 'empty'}")

        self.transport.write_data_bytes(loop_length)
        rep = self._read_cmd_packet()
        if not rep or rep[0] != 0x85:
            raise RuntimeError(f"Import length failed: {rep.hex() if rep else 'empty'}")

        sent = 0
        with open(pcm_path, "rb") as f:
            for i in range(total_frames):
                chunk = f.read(DATA_REPORT_SIZE)
                if not chunk:
                    break

                page = i + 1
                self.transport.write_command_bytes(pack_command(CMD_UPLOAD_AUDIO, loop_index + struct.pack("<I", page)))
                rep = self._read_cmd_packet()
                if not rep or rep[0] != 0x85:
                    raise RuntimeError(f"Import page {page} command failed: {rep.hex() if rep else 'empty'}")

                if len(chunk) < DATA_REPORT_SIZE:
                    chunk += bytes(DATA_REPORT_SIZE - len(chunk))

                self.transport.write_data_bytes(chunk)
                rep = self._read_cmd_packet()
                if not rep or rep[0] != 0x85:
                    raise RuntimeError(f"Import page {page} data failed: {rep.hex() if rep else 'empty'}")

                sent += min(DATA_REPORT_SIZE, read_size - sent)
                if progress:
                    progress(min(100, int(sent / read_size * 100)))

        return self.get_loop_info(index)

    def import_audio(
        self,
        index: int,
        input_path: Path,
        progress: Optional[ProgressCallback] = None,
        quiet: bool = False,
        normalize: bool = False,
        preset: str = "standard",
    ) -> LoopInfo:
        tmp_path = prepare_import_audio(Path(input_path), quiet=quiet, normalize=normalize, preset=preset)
        try:
            return self.import_pcm24le_stereo(index, tmp_path, progress=progress)
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                pass

    def backup_slots(self, destination: Path, slots: list[int], progress: Optional[Callable[[int], None]] = None) -> Path:
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        info = self.info()
        exported = []

        present_slots = []
        for slot in slots:
            loop = self.get_loop_info(slot)
            if loop.present:
                present_slots.append(loop)

        for i, loop in enumerate(present_slots):
            name = f"slot{loop.index:02d}.wav"
            self.export_wav(loop.index, destination / name)
            exported.append({"slot": loop.index, "file": name, "bytes": loop.data_length})
            if progress:
                progress(int((i + 1) / max(1, len(present_slots)) * 100))

        manifest = {
            "device": asdict(info),
            "loops": exported,
        }
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return destination

    def backup(self, destination: Path, progress: Optional[Callable[[int], None]] = None) -> Path:
        return self.backup_slots(destination, list(range(100)), progress=progress)
