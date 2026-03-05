#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKETCH_DIR="$ROOT_DIR/firmware/tankctl_device"
FQBN="arduino:renesas_uno:unor4wifi"
BUILD_DIR="$ROOT_DIR/.build/firmware"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli is not installed or not in PATH"
  echo "Install locally with:"
  echo "  mkdir -p ~/.local/bin"
  echo "  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=~/.local/bin sh"
  echo "  export PATH=\"$HOME/.local/bin:$PATH\""
  exit 1
fi

mkdir -p "$BUILD_DIR"

arduino-cli core update-index
arduino-cli core install arduino:renesas_uno
arduino-cli lib install "ArduinoJson" "PubSubClient" "NTPClient" "OneWire" "DallasTemperature"

arduino-cli compile \
  --fqbn "$FQBN" \
  --warnings all \
  --build-path "$BUILD_DIR" \
  "$SKETCH_DIR"

echo "Firmware compile successful for $FQBN"
