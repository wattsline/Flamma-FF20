#!/usr/bin/env bash
set -euo pipefail

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok() { printf "✓ %s\n" "$*"; }
fail() { printf "✗ %s\n" "$*" >&2; exit 1; }

bold "Updating FF20 Tools"

if [[ -d .git ]]; then
  git pull
  ok "Repository updated"
else
  ok "No git repository detected; reinstalling current source tree"
fi

if [[ ! -d .venv ]]; then
  fail ".venv not found. Run ./install.sh first."
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[gui]"
ff20 --help >/dev/null
ok "Package update complete"

if [[ "$(uname -s)" == "Darwin" && -x ./create_macos_app.sh ]]; then
  ./create_macos_app.sh
  ok "macOS app launcher refreshed"
fi

echo
echo "Update complete."
