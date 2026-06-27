# Changelog

## FF20 Tools 1.0.0

Initial stable release.

### Added

- Native FF20 USB/HID protocol implementation
- CLI command: `ff20`
- GUI command: `ff20-gui`
- Device discovery and info
- Loop listing
- WAV export
- Audio/WAV import
- Loudness normalization on import
- Multi-select GUI actions
- Backup selected slots with manifest
- Friendly CLI and GUI error handling
- macOS installer/update/uninstall helper scripts
- `ff20 doctor` diagnostic command
- Protocol documentation

## FF20 Tools v1.0.1

### Overview

This is the first maintenance release following the initial public release of FF20 Tools. It focuses on improving reliability, installation, and the overall user experience without changing the core workflow.

### New

* Added application branding to the GUI using the FF20 Tools icon.
* Added application window icon for a more polished desktop experience.
* Renamed the macOS application to FF20 Tools.app.

### Improvements

* Improved macOS application launcher.
* Improved installer robustness.
* Improved update script.
* Better detection of Python virtual environments (python3 vs python).
* Better handling of Homebrew installations.
* Better detection of FFmpeg on Apple Silicon and Intel Macs.
* Improved error reporting when required dependencies are missing.
* Cleaner startup experience for applications launched from Finder.

### Bug Fixes

* Fixed importing audio when launching the application from the macOS application icon.
* Fixed failures caused by Finder not inheriting the user’s shell PATH.
* Fixed scripts assuming .venv/bin/python always exists.
* Improved compatibility with Python 3.14 virtual environments.
* Improved macOS application bundle generation.

### Installer

The installer now:

* Verifies Xcode Command Line Tools.
* Detects or installs Homebrew when necessary.
* Detects or installs Python automatically.
* Creates the virtual environment.
* Installs all required Python dependencies.
* Installs FFmpeg and HIDAPI.
* Runs a post-install smoke test.
* Optionally creates the macOS application launcher.

### Compatibility

Tested on:

* macOS Tahoe
* Apple Silicon (Homebrew)
* Python 3.14
* Flamma FF20 Firmware B1.0.0

### Upgrade

Existing users can update by running:

./update.sh

or perform a clean installation using:

./install.sh

T### hanks

Thank you to everyone testing the project and providing feedback. Real-world testing continues to drive the direction of FF20 Tools.