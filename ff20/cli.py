from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .constants import BYTES_PER_FRAME_24BIT_STEREO, SAMPLE_RATE
from .exceptions import FF20Error
from .pedal import FF20Pedal


def parse_slots(value: str) -> list[int]:
    slots = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            slots.extend(range(start, end + 1))
        else:
            slots.append(int(part))
    return sorted(set(slots))


def cmd_devices(args) -> None:
    devs = FF20Pedal.devices()
    if not devs:
        print("No FF20 HID devices found")
        return
    for d in devs:
        print(
            f"VID=0x{d.get('vendor_id', 0):04X} "
            f"PID=0x{d.get('product_id', 0):04X} "
            f"iface={d.get('interface_number')} "
            f"product={d.get('product_string') or d.get('product')} "
            f"serial={d.get('serial_number')}"
        )


def cmd_info(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        info = pedal.info()
    for k, v in info.__dict__.items():
        print(f"{k}: {v}")


def cmd_list(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        loops = pedal.list_loops(args.count)
    print(f"{'slot':>4} {'present':>7} {'bytes':>12} {'minutes':>9} {'status':>6} {'export':>6}")
    for item in loops:
        print(
            f"{item.index:>4} "
            f"{('yes' if item.present else 'no'):>7} "
            f"{item.data_length:>12} "
            f"{item.minutes:>9.2f} "
            f"{item.status_flag:>6} "
            f"{item.export_flag:>6}"
        )


def cmd_export(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        out = pedal.export_wav(
            args.index,
            Path(args.output),
            progress=None if args.quiet else lambda p: print(f"\rExporting: {p:3d}%", end="", flush=True),
        )
    if not args.quiet:
        print()
    print(f"Exported: {out}")


def cmd_import(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        info = pedal.import_audio(
            args.index,
            Path(args.input),
            progress=None if args.quiet else lambda p: print(f"\rImporting: {p:3d}%", end="", flush=True),
            quiet=args.quiet,
            normalize=args.normalize,
            preset=args.preset,
        )
    if not args.quiet:
        print()
    print(f"Imported slot {info.index}: bytes={info.data_length} minutes={info.minutes:.2f}")


def cmd_delete(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        pedal.delete_loop(args.index)
    print(f"Deleted slot {args.index}")


def cmd_space(args) -> None:
    with FF20Pedal(args.serial, args.verbose) as pedal:
        free = pedal.query_free_bytes()
    minutes = free / BYTES_PER_FRAME_24BIT_STEREO / SAMPLE_RATE / 60
    print(f"free_bytes: {free}")
    print(f"free_minutes: {minutes:.2f}")


def cmd_backup(args) -> None:
    slots = parse_slots(args.slots) if args.slots else list(range(100))
    with FF20Pedal(args.serial, args.verbose) as pedal:
        dest = pedal.backup_slots(Path(args.destination), slots, progress=lambda p: print(f"\rBacking up: {p:3d}%", end="", flush=True))
    print()
    print(f"Backup complete: {dest}")



def _check_program(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    if not path:
        return False, "not found"
    try:
        proc = subprocess.run([name, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        first = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr).splitlines() else path
        return True, first
    except Exception:
        return True, path


def cmd_doctor(args) -> None:
    print("FF20 Tools Doctor")
    print("==================")
    print()
    print("Python")
    print(f"  ✓ {sys.version.split()[0]}")
    print()

    print("External tools")
    for program in ["ffmpeg"]:
        ok, detail = _check_program(program)
        print(f"  {'✓' if ok else '✗'} {program}: {detail}")
    print()

    print("Python packages")
    try:
        import hid
        print(f"  ✓ hid: {getattr(hid, '__file__', 'installed')}")
    except Exception as e:
        print(f"  ✗ hid: {e}")

    try:
        import PySide6
        print(f"  ✓ PySide6: {getattr(PySide6, '__version__', 'installed')}")
    except Exception as e:
        print(f"  ✗ PySide6: {e}")
    print()

    print("USB")
    devs = FF20Pedal.devices()
    if not devs:
        print("  ⚪ No FF20 pedal detected")
    else:
        cmd_iface = any(d.get("interface_number") == 0 for d in devs)
        data_iface = any(d.get("interface_number") == 1 for d in devs)
        print(f"  ✓ FF20 HID entries: {len(devs)}")
        print(f"  {'✓' if cmd_iface else '✗'} Command interface")
        print(f"  {'✓' if data_iface else '✗'} Data interface")
    print()

    if devs:
        try:
            with FF20Pedal(args.serial, args.verbose) as pedal:
                info = pedal.info()
            print("Device")
            print(f"  ✓ Product: {info.product}")
            print(f"  ✓ Serial: {info.serial}")
            print(f"  ✓ App: {info.app_version}")
            print(f"  ✓ Boot: {info.boot_version}")
        except FF20Error as e:
            print("Device")
            print(f"  ✗ {e}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Native CLI for Flamma FF20")
    p.add_argument("--serial", help="FF20 serial number, if multiple pedals are connected")
    p.add_argument("-v", "--verbose", action="store_true", help="Print HID debug trace")
    sub = p.add_subparsers(dest="cmd", required=True)

    x = sub.add_parser("devices", help="List FF20 HID interfaces")
    x.set_defaults(func=cmd_devices)

    x = sub.add_parser("info", help="Read device info")
    x.set_defaults(func=cmd_info)

    x = sub.add_parser("list", help="List loop slots")
    x.add_argument("--count", type=int, default=100)
    x.set_defaults(func=cmd_list)

    x = sub.add_parser("export", help="Export a loop slot to WAV")
    x.add_argument("index", type=int)
    x.add_argument("output")
    x.add_argument("-q", "--quiet", action="store_true")
    x.set_defaults(func=cmd_export)

    x = sub.add_parser("import", help="Import an audio file into a slot")
    x.add_argument("index", type=int)
    x.add_argument("input")
    x.add_argument("-q", "--quiet", action="store_true")
    x.add_argument("--normalize", action="store_true", help="Loudness-normalize before import")
    x.add_argument("--preset", choices=["conservative", "standard", "hot"], default="standard")
    x.set_defaults(func=cmd_import)

    x = sub.add_parser("delete", help="Delete a loop slot")
    x.add_argument("index", type=int)
    x.set_defaults(func=cmd_delete)

    x = sub.add_parser("space", help="Show estimated remaining capacity")
    x.set_defaults(func=cmd_space)

    x = sub.add_parser("backup", help="Export present loops and manifest")
    x.add_argument("destination")
    x.add_argument("--slots", help="Comma/range slot list, e.g. 0,1,5-8")
    x.set_defaults(func=cmd_backup)


    x = sub.add_parser("doctor", help="Run system and FF20 readiness checks")
    x.set_defaults(func=cmd_doctor)

    return p


def main() -> None:
    try:
        args = build_parser().parse_args()
        args.func(args)
    except FF20Error as e:
        print(f"\nFF20: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
