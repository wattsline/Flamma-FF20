# FF20 Tools

Native, cross-platform tools for the Flamma FF20 looper pedal.

The official Flamma FF20 desktop app is an Intel Electron app for macOS, but it requires Rosetta on Apple Silicon, which will **soon be removed from macOS.** `FF20 Tools` offers a native Python implementation of the FF20 USB/HID protocol, complete with a command-line interface (CLI) and PySide6 GUI, making it **compatible with both Intel and Apple Silicon platforms.**


<p align="center">
  <img src="./Resources/Flamma FF20.png" alt="Flamma FF20 Looper + Drums" width="300" height="245">
</p>
<p align="center">
  <img src="./Resources/FF20 Tools Screenshot.png" alt="Flamma FF20 Looper + Drums" width="700" height="519">
</p>

## Status: v1.0.1

Validated features:

- Device discovery
- Device/version info
- Loop slot listing
- WAV export
- WAV/audio import
- Loudness normalization on import
- Delete selected loops
- Multi-select export/import/delete/backup
- Backup selected loops with manifest
- Polished Qt GUI with friendly unplugged-pedal messages
- macOS installer/update/uninstall helper scripts
- "One Click" Launcher icon in ~/Applications

## Requirements

For macOS:

- Apple Silicon or Intel Mac
- Python 3.10+
- Xcode Command Line Tools (Homebrew pre-req)
- Homebrew
- `hidapi`
- `ffmpeg`

The installer checks and installs the required Homebrew packages.

## Quick install

```bash
./install.sh
```

Then launch:

```bash
source .venv/bin/activate
ff20-gui
```

Or use the CLI:

```bash
ff20 info
ff20 list
```

## Manual install

```bash
brew install hidapi ffmpeg
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[gui]"
```

## CLI examples

```bash
ff20 devices
ff20 info
ff20 list
ff20 export 0 slot00.wav
ff20 import 0 loop.wav
ff20 import 0 loop.wav --normalize --preset standard
ff20 delete 0
ff20 backup ~/FF20-Backup --slots 0,1,2
```

## GUI

```bash
ff20-gui
```

## Update

```bash
./update.sh
```

## Uninstall local environment

```bash
./uninstall.sh
```

This removes the local virtual environment only. It does not uninstall Homebrew, Python, hidapi, or ffmpeg.


## Important note about pedal behavior

A loop recorded on the pedal must be **saved on the pedal** before it becomes exportable through USB.


## Normalization presets

| Preset | Integrated loudness | True peak | Use |
|---|---:|---:|---|
| conservative | -18 LUFS | -2.0 dBTP | Safer, lower level |
| standard | -16 LUFS | -1.5 dBTP | General live use |
| hot | -14 LUFS | -1.0 dBTP | Louder loops |

## Troubleshooting

If the pedal is unplugged or unavailable, CLI commands should show a friendly message such as:

```text
FF20: No FF20 pedal was detected.
```

In the GUI, use **Refresh Connection** after connecting the pedal.

For installation problems, rerun:

```bash
./install.sh
```

For a quick runtime test:

```bash
source .venv/bin/activate
ff20 --help
ff20 devices
```

## Acknowledgements

This project was developed through hands-on testing with a real Flamma FF20 pedal, careful inspection of the vendor Electron application, and iterative validation of the FF20 USB HID protocol.

Special thanks to **Ken Watts** for the original problem statement, protocol exploration, testing on Apple Silicon, identifying the pedal's saved-loop behavior, validating import/export/normalization, and shaping the project around real musician workflow rather than feature-chasing.

The project exists because musicians need reliable, long-lived tools that continue working even when vendor applications depend on aging runtimes such as Rosetta.

## Disclaimer

This project is not affiliated with Flamma.
