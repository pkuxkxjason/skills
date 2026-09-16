#!/usr/bin/env bash
# 把封面 HTML 截成 png（headless Chrome）。
# 用法: bash make_cover.sh <cover.html> <out.png> [width] [height]
set -euo pipefail
HTML="${1:?cover.html}"; OUT="${2:?out.png}"; W="${3:-1920}"; H="${4:-1080}"
CHROME="$(ls -t "$HOME"/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell 2>/dev/null | head -1)"
if [ -z "${CHROME:-}" ]; then
  echo "找不到 chrome-headless-shell。可先跑: npx puppeteer browsers install chrome-headless-shell"; exit 1
fi
abs="$(cd "$(dirname "$HTML")" && pwd)/$(basename "$HTML")"
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --virtual-time-budget=5000 \
  --window-size="${W},${H}" --screenshot="$OUT" "file://${abs}"
echo "wrote $OUT (${W}x${H})"