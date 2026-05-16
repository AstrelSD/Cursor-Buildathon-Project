#!/bin/sh
set -e

# Dev image skips `npm ci` at build time (avoids long/failed Docker build network).
# Install into the named node_modules volume on first start or after lockfile changes.
MARKER="node_modules/.package-lock.hash"
CURRENT="$(sha256sum package-lock.json | awk '{print $1}')"

needs_install=0
if [ ! -f "$MARKER" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$CURRENT" ]; then
  needs_install=1
elif [ ! -d node_modules/@supabase/ssr ] || [ ! -d node_modules/next ]; then
  echo "node_modules volume is missing packages; reinstalling..."
  needs_install=1
fi

if [ "$needs_install" -eq 1 ]; then
  echo "Installing frontend dependencies (npm ci)..."
  npm ci --no-audit --no-fund
  echo "$CURRENT" > "$MARKER"
fi

exec "$@"
