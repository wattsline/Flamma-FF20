# Fresh install smoke test

Use this on a new Mac to test from scratch.

## 1. Unzip

```bash
unzip ff20-tools-v1.0.0.zip
cd ff20-tools-v1.0.0
```

## 2. Run installer

```bash
./install.sh
```

The installer checks for:

- Xcode Command Line Tools
- Homebrew
- hidapi
- ffmpeg
- Python 3.10+
- local virtual environment
- package installation

## 3. Test without pedal

```bash
source .venv/bin/activate
ff20 info
```

Expected:

```text
FF20: No FF20 pedal was detected.
```

## 4. Run doctor

```bash
ff20 doctor
```

If the pedal is disconnected, the USB section should report no pedal detected without crashing.

## 5. Connect pedal

Connect the FF20 using USB-C, then run:

```bash
ff20 devices
ff20 info
ff20 list --count 10
ff20 doctor
```

## 6. GUI

```bash
ff20-gui
```

Expected:

- Yellow "Connecting..."
- Green "Connected"
- Slots table loads
- Empty slots shown with gray circle
- Present slots shown with green dot

## 7. Roundtrip import/export test

```bash
ff20 import 0 /path/to/test.wav --normalize --preset standard
ff20 export 0 /tmp/ff20_roundtrip.wav
open /tmp/ff20_roundtrip.wav
```

## 8. Update

```bash
./update.sh
```

## 9. Remove local environment

```bash
./uninstall.sh
```
