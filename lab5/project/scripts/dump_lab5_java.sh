#!/usr/bin/env bash
# Друк усіх Java-файлів практикуму (src/) у форматі === path === / вміст.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT_DIR/src"
if [[ ! -d "$SRC" ]]; then
  echo "No src directory: $SRC" >&2
  exit 1
fi
cd "$SRC"
find . -name '*.java' -print | LC_ALL=C sort | while IFS= read -r rel; do
  rel="${rel#./}"
  echo "=== ${rel} ==="
  cat "./$rel"
  echo
done
