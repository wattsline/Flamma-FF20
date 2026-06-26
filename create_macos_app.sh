#!/usr/bin/env bash
set -euo pipefail

APP_NAME="FF20 Tools"
APP_BUNDLE="${APP_NAME}.app"
DEFAULT_INSTALL_DIR="$HOME/Applications"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
ICON_SOURCE="$PROJECT_DIR/Resources/FF20.icns"

ok() { printf "✓ %s\n" "$*"; }
warn() { printf "⚠ %s\n" "$*"; }
fail() { printf "✗ %s\n" "$*" >&2; exit 1; }

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "macOS app bundle creation is only supported on macOS."
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  fail "Virtual environment not found at $VENV_PYTHON. Run ./install.sh first."
fi

INSTALL_DIR="${1:-$DEFAULT_INSTALL_DIR}"
mkdir -p "$INSTALL_DIR"

APP_PATH="$INSTALL_DIR/$APP_BUNDLE"
CONTENTS="$APP_PATH/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

rm -rf "$APP_PATH"
mkdir -p "$MACOS" "$RESOURCES"

cat > "$MACOS/ff20-native-launcher" <<EOF
#!/usr/bin/env bash
cd "$PROJECT_DIR"
exec "$VENV_PYTHON" -m ff20.gui.app
EOF

chmod +x "$MACOS/ff20-native-launcher"

if [[ -f "$ICON_SOURCE" ]]; then
  cp "$ICON_SOURCE" "$RESOURCES/FF20.icns"
  ICON_PLIST_BLOCK='
    <key>CFBundleIconFile</key>
    <string>FF20</string>'
  ok "Installed icon from Resources/FF20.icns"
else
  ICON_PLIST_BLOCK=""
  warn "Resources/FF20.icns not found; creating app without custom icon."
fi

cat > "$CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>CFBundleName</key>
    <string>FF20 Tools</string>
    <key>CFBundleDisplayName</key>
    <string>FF20 Tools</string>
    <key>CFBundleIdentifier</key>
    <string>org.ff20tools.native</string>
    <key>CFBundleVersion</key>
    <string>1.0.1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.1</string>
    <key>CFBundleExecutable</key>
    <string>ff20-native-launcher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>$ICON_PLIST_BLOCK
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
  </dict>
</plist>
EOF

xattr -dr com.apple.quarantine "$APP_PATH" 2>/dev/null || true
touch "$APP_PATH"
touch "$CONTENTS/Info.plist"

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -f "$APP_PATH" >/dev/null 2>&1 || true

ok "Created $APP_PATH"

echo
echo "If Finder still shows the old generic icon:"
echo
echo "  1. Quit and reopen Finder, or run: killall Finder"
echo "  2. Remove the app from Dock and add it again"
echo "  3. In rare cases, reboot clears the icon cache"
echo
echo "Launch from:"
echo
echo "    $APP_PATH"
