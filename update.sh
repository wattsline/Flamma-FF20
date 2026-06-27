#!/usr/bin/env bash
set -euo pipefail

ok() { printf "✓ %s\n" "$*"; }
fail() { printf "✗ %s\n" "$*" >&2; exit 1; }

find_venv_python() {
  if [[ -x ".venv/bin/python3" ]]; then echo ".venv/bin/python3";
  elif [[ -x ".venv/bin/python" ]]; then echo ".venv/bin/python";
  else echo ""; fi
}

echo "Updating FF20 Tools"

if [[ -d .git ]]; then git pull; ok "Repository updated";
else ok "No git repository detected; reinstalling current source tree"; fi

[[ -d .venv ]] || fail ".venv not found. Run ./install.sh first."
VENV_PYTHON="$(find_venv_python)"
[[ -n "$VENV_PYTHON" ]] || fail "Could not find .venv/bin/python3 or .venv/bin/python"

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -e ".[gui]"
.venv/bin/ff20 --help >/dev/null
ok "Package update complete"

if [[ "$(uname -s)" == "Darwin" && -x ./create_macos_app.sh ]]; then
  ./create_macos_app.sh
  ok "macOS app launcher refreshed"
fi
