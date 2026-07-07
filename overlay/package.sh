#!/usr/bin/env bash
# Package overlay/ into a zip suitable for upload to the Twitch Developer
# Console (Extensions > Asset Hosting). Excludes local-test-only files
# (*.local-test.*) so viewers never receive the dev/mock harness.
set -euo pipefail

OVERLAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$OVERLAY_DIR/../dist/extension.zip}"

mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
rm -f "$OUT"

cd "$OVERLAY_DIR"
zip -r "$OUT" . \
  -x '*.local-test.*' \
  -x 'package.sh' \
  -x '.DS_Store' -x '*/.DS_Store'

echo "Wrote $OUT"
unzip -l "$OUT"
