#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKETCH_DIR="$ROOT_DIR/firmware/tankctl_device"
FQBN="arduino:renesas_uno:unor4wifi"
BUILD_DIR="$ROOT_DIR/.build/firmware"
PORT="${1:-}"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli is not installed or not in PATH"
  echo "Install locally with:"
  echo "  mkdir -p ~/.local/bin"
  echo "  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=~/.local/bin sh"
  echo "  export PATH=\"$HOME/.local/bin:$PATH\""
  exit 1
fi

if [[ -z "$PORT" ]]; then
  # Try to find UNO R4 WiFi by name first
  PORT="$(arduino-cli board list | awk 'NR>1 && tolower($0) ~ /uno r4 wifi|unowifir4/ {print $1; exit}')"
  
  # If not found, try any ttyACM, ttyUSB, or ttyAMA device
  if [[ -z "$PORT" ]]; then
    PORT="$(arduino-cli board list | awk 'NR>1 && $1 ~ /ttyACM|ttyUSB|ttyAMA/ {print $1; exit}')"
  fi
  
  # Last resort: check /dev directly
  if [[ -z "$PORT" ]]; then
    for dev in /dev/ttyACM0 /dev/ttyUSB0 /dev/ttyAMA0; do
      if [[ -e "$dev" ]]; then
        PORT="$dev"
        break
      fi
    done
  fi
fi

if [[ -z "$PORT" ]]; then
  echo "Could not auto-detect an Arduino serial port."
  echo "Available ports:"
  arduino-cli board list
  echo ""
  echo "Upload manually with: ./tools/upload_firmware.sh <serial-port>"
  exit 1
fi

echo "Using serial port: $PORT"

echo "Compiling firmware first..."
"$ROOT_DIR/tools/build_firmware.sh"

echo "Uploading firmware to $PORT..."
arduino-cli upload \
  --fqbn "$FQBN" \
  --port "$PORT" \
  --input-dir "$BUILD_DIR" \
  "$SKETCH_DIR"

echo "Firmware upload successful"
