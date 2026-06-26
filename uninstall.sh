#!/usr/bin/env bash
set -euo pipefail

APP_PATH="$HOME/Applications/FF20 Native.app"

echo "This removes the local .venv virtual environment and optionally the macOS app launcher."
echo "It will not remove Homebrew, Python, hidapi, or ffmpeg."
read -r -p "Continue? [y/N] " answer

if [[ "$answer" =~ ^[Yy]$ ]]; then
  rm -rf .venv
  echo "✓ Removed .venv"

  if [[ -d "$APP_PATH" ]]; then
    read -r -p "Remove $APP_PATH? [Y/n] " remove_app
    remove_app="${remove_app:-Y}"
    if [[ "$remove_app" =~ ^[Yy]$ ]]; then
      rm -rf "$APP_PATH"
      echo "✓ Removed $APP_PATH"
    fi
  fi
else
  echo "Cancelled."
fi
