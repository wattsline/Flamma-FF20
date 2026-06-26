#!/usr/bin/env bash
set -u

APP_NAME="FF20 Tools"
MIN_PY_MAJOR=3
MIN_PY_MINOR=10

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok() { printf "✓ %s\n" "$*"; }
warn() { printf "⚠ %s\n" "$*"; }
fail() { printf "✗ %s\n" "$*" >&2; exit 1; }

section() {
  printf "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
  bold "$*"
  printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
}

run_or_fail() {
  "$@"
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    fail "Command failed: $*"
  fi
}

load_homebrew_env() {
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_homebrew_if_missing() {
  load_homebrew_env

  if command -v brew >/dev/null 2>&1; then
    ok "Homebrew found: $(brew --version | head -1)"
    return
  fi

  warn "Homebrew is not installed."
  read -r -p "Install Homebrew now? [Y/n] " answer
  answer="${answer:-Y}"

  if [[ "$answer" =~ ^[Yy]$ ]]; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    load_homebrew_env
  else
    fail "Homebrew is required. Install it, then rerun ./install.sh."
  fi

  command -v brew >/dev/null 2>&1 || fail "Homebrew installed but not found in PATH. Open a new terminal and rerun ./install.sh."
  ok "Homebrew installed"
}

check_command_line_tools() {
  if ! xcode-select -p >/dev/null 2>&1; then
    warn "Xcode Command Line Tools are not installed."
    echo "Launching Apple's installer. Re-run ./install.sh after it completes."
    xcode-select --install || true
    exit 1
  fi
  ok "Xcode Command Line Tools found"
}

install_brew_package() {
  local pkg="$1"
  if brew list "$pkg" >/dev/null 2>&1; then
    ok "$pkg already installed"
  else
    echo "Installing $pkg..."
    run_or_fail brew install "$pkg"
    ok "$pkg installed"
  fi
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
  elif command -v python >/dev/null 2>&1; then
    command -v python
  else
    echo ""
  fi
}

python_ok() {
  local py="$1"
  "$py" - <<PY >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] >= (${MIN_PY_MAJOR}, ${MIN_PY_MINOR}) else 1)
PY
}

check_python() {
  local py
  py="$(find_python)"

  if [[ -z "$py" ]] || ! python_ok "$py"; then
    warn "Python 3.${MIN_PY_MINOR}+ not found. Installing Homebrew Python..."
    run_or_fail brew install python
    load_homebrew_env
    py="$(find_python)"
  fi

  [[ -n "$py" ]] || fail "Python not found after installation."
  python_ok "$py" || fail "Python is still too old: $("$py" --version)"

  PYTHON_BIN="$py"
  ok "Python found: $("$PYTHON_BIN" --version)"
}

create_venv_and_install() {
  section "Creating virtual environment"

  if [[ ! -f "pyproject.toml" ]]; then
    fail "pyproject.toml not found. Run install.sh from the ff20-tools project directory."
  fi

  if [[ ! -d ".venv" ]]; then
    run_or_fail "$PYTHON_BIN" -m venv .venv
    ok "Virtual environment created"
  else
    ok "Virtual environment already exists"
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate || fail "Could not activate .venv"

  run_or_fail python -m pip install --upgrade pip
  run_or_fail python -m pip install -e ".[gui]"
  ok "ff20-tools installed into .venv"
}

smoke_test() {
  section "Smoke test"

  # shellcheck disable=SC1091
  source .venv/bin/activate || fail "Could not activate .venv"

  run_or_fail ff20 --help >/dev/null
  ok "CLI command available"

  if ff20 devices 2>/dev/null | grep -q "FF20"; then
    ok "FF20 pedal detected"
  else
    warn "No FF20 pedal detected. This is OK if the pedal is not connected."
  fi
}

create_app_launcher() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    return
  fi

  section "macOS application launcher"

  read -r -p "Create FF20 Native.app in ~/Applications? [Y/n] " answer
  answer="${answer:-Y}"

  if [[ "$answer" =~ ^[Yy]$ ]]; then
    if [[ -x "./create_macos_app.sh" ]]; then
      run_or_fail ./create_macos_app.sh
    else
      warn "create_macos_app.sh not found; skipping app launcher."
    fi
  else
    warn "Skipping macOS app launcher."
  fi
}

section "$APP_NAME Installer v1.0.1"

if [[ "$(uname -s)" == "Darwin" ]]; then
  ok "macOS detected: $(sw_vers -productVersion)"
  check_command_line_tools
  install_homebrew_if_missing

  section "Installing Homebrew dependencies"
  install_brew_package hidapi
  install_brew_package ffmpeg
else
  warn "Non-macOS detected. Linux support is experimental."
  warn "Install hidapi, ffmpeg, and Python 3 manually before continuing."
fi

section "Checking Python"
check_python

create_venv_and_install
smoke_test
create_app_launcher

section "Installation complete"

cat <<'EOF'
To launch the GUI from Terminal:

    source .venv/bin/activate
    ff20-gui

To use the CLI:

    source .venv/bin/activate
    ff20 info
    ff20 list

If you created the macOS launcher, open:

    ~/Applications/FF20 Native.app

or search for "FF20 Native" in Spotlight.
EOF
