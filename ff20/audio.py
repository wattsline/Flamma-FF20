from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .constants import CHANNELS, SAMPLE_RATE

import shutil
from .exceptions import FF20Error

from .system import find_ffmpeg

@dataclass(frozen=True)
class LoudnessPreset:
    name: str
    integrated_lufs: float
    true_peak_db: float
    lra: float


LOUDNESS_PRESETS = {
    "conservative": LoudnessPreset("conservative", -18.0, -2.0, 11.0),
    "standard": LoudnessPreset("standard", -16.0, -1.5, 11.0),
    "hot": LoudnessPreset("hot", -14.0, -1.0, 9.0),
}


def find_ffmpeg() -> str:
    candidates = [
        shutil.which("ffmpeg"),
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    raise FF20Error(
        "ffmpeg was not found.\n\n"
        "Install it with:\n"
        "  brew install ffmpeg\n\n"
        "Then restart FF20 Native."
    )


def run_ffmpeg(cmd: list[str]) -> None:
    cmd = list(cmd)
    cmd[0] = find_ffmpeg()
    subprocess.run(cmd, check=True)

def analyze_loudness(input_path: Path) -> dict:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i", str(input_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null",
        "-",
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    text = proc.stderr
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Could not parse ffmpeg loudnorm output:\n{text}")
    return json.loads(text[start:end + 1])


def normalize_audio(input_path: Path, output_path: Path, preset: str = "standard", two_pass: bool = True) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if preset not in LOUDNESS_PRESETS:
        raise ValueError(f"Unknown loudness preset {preset!r}. Options: {', '.join(LOUDNESS_PRESETS)}")

    p = LOUDNESS_PRESETS[preset]

    if two_pass:
        measured = analyze_loudness(input_path)
        af = (
            f"loudnorm=I={p.integrated_lufs}:TP={p.true_peak_db}:LRA={p.lra}:"
            f"measured_I={measured['input_i']}:"
            f"measured_TP={measured['input_tp']}:"
            f"measured_LRA={measured['input_lra']}:"
            f"measured_thresh={measured['input_thresh']}:"
            f"offset={measured['target_offset']}:"
            f"linear=true:print_format=summary"
        )
    else:
        af = f"loudnorm=I={p.integrated_lufs}:TP={p.true_peak_db}:LRA={p.lra}:print_format=summary"

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i", str(input_path),
        "-af", af,
        "-ac", str(CHANNELS),
        "-ar", str(SAMPLE_RATE),
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path


def convert_to_s24le(input_path: Path, quiet: bool = False) -> Path:
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    with tempfile.NamedTemporaryFile(prefix="ff20_import_", suffix=".s24le", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner",
            "-loglevel", "error" if quiet else "info",
            "-i", str(input_path),
            "-ac", str(CHANNELS),
            "-ar", str(SAMPLE_RATE),
            "-acodec", "pcm_s24le",
            "-f", "s24le",
            str(tmp_path),
        ]
        run_ffmpeg(cmd)
        return tmp_path
    except Exception:
        try:
            tmp_path.unlink()
        except Exception:
            pass
        raise


def prepare_import_audio(input_path: Path, quiet: bool = False, normalize: bool = False, preset: str = "standard") -> Path:
    input_path = Path(input_path)

    if not normalize:
        return convert_to_s24le(input_path, quiet=quiet)

    with tempfile.NamedTemporaryFile(prefix="ff20_normalized_", suffix=".wav", delete=False) as tmp:
        normalized_path = Path(tmp.name)

    try:
        normalize_audio(input_path, normalized_path, preset=preset)
        return convert_to_s24le(normalized_path, quiet=quiet)
    finally:
        try:
            normalized_path.unlink()
        except Exception:
            pass


def write_vendor_style_wav_header(wf) -> None:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(4)
    wf.setframerate(SAMPLE_RATE)


def expand_s24le_to_vendor_s32le(data: bytes) -> tuple[bytes, bytes]:
    sample_len = len(data) // 3
    cache = data[sample_len * 3:]
    buf = bytearray(sample_len * 4)
    for i in range(sample_len):
        temp = data[i * 3:i * 3 + 3]
        buf[i * 4:i * 4 + 4] = b"\x00" + temp
    return bytes(buf), cache
