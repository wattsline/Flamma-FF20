from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .exceptions import FF20Error


def find_executable(name: str, candidates: tuple[str, ...]) -> str | None:
    found = shutil.which(name)
    if found:
        return found

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    return None


def find_ffmpeg() -> str:
    path = find_executable(
        "ffmpeg",
        (
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
        ),
    )

    if path:
        return path

    raise FF20Error(
        "ffmpeg was not found.\n\n"
        "Install it with:\n"
        "  brew install ffmpeg\n\n"
        "Then restart FF20 Tools."
    )


def command_version(command: str) -> str:
    try:
        proc = subprocess.run(
            [command, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        lines = (proc.stdout or proc.stderr).splitlines()
        return lines[0] if lines else command
    except Exception as exc:
        return f"{command}: {exc}"


def python_version() -> str:
    return sys.version.split()[0]
