#!/usr/bin/env bash
set -euo pipefail

APP_NAME="FF20 Tools"
APP_BUNDLE="${APP_NAME}.app"
DEFAULT_INSTALL_DIR="$HOME/Applications"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_SOURCE="$PROJECT_DIR/Resources/FF20.icns"

ok() { printf "✓ %s\n" "$*"; }
warn() { printf "⚠ %s\n" "$*"; }
fail() { printf "✗ %s\n" "$*" >&2; exit 1; }

find_venv_python() {
  if [[ -x "$PROJECT_DIR/.venv/bin/python3" ]]; then
    echo "$PROJECT_DIR/.venv/bin/python3"
  elif [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    echo "$PROJECT_DIR/.venv/bin/python"
  else
    echo ""
  fi
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "macOS app bundle creation is only supported on macOS."
fi

VENV_PYTHON="$(find_venv_python)"
if [[ -z "$VENV_PYTHON" ]]; then
  fail "Virtual environment Python not found. Run ./install.sh first."
fi

INSTALL_DIR="${1:-$DEFAULT_INSTALL_DIR}"
mkdir -p "$INSTALL_DIR"

APP_PATH="$INSTALL_DIR/$APP_BUNDLE"
CONTENTS="$APP_PATH/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

rm -rf "$APP_PATH"
mkdir -p "$MACOS" "$RESOURCES"

cat > "$MACOS/ff20-tools-launcher" <<EOF
#!/usr/bin/env bash
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/opt/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:\$PATH"
exec "$VENV_PYTHON" -m ff20.gui.app
EOF

chmod +x "$MACOS/ff20-tools-launcher"

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
    <string>org.ff20tools.tools</string>
    <key>CFBundleVersion</key>
    <string>1.0.1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.1</string>
    <key>CFBundleExecutable</key>
    <string>ff20-tools-launcher</string>
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
touch "$APP_PATH" "$CONTENTS/Info.plist"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_PATH" >/dev/null 2>&1 || true
ok "Created $APP_PATH"
