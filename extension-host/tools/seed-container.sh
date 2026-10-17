#!/usr/bin/env bash
# Copies the host's data (upstream catalog, local build index, state) into the compose volume.
# The container runs as uid 10001, so the copy is chowned to it. Run after tools/fetch-upstream.py.
# Usage: seed-container.sh [volume-name]   (default: kuroibara_extension_host_data)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VOL="${1:-kuroibara_extension_host_data}"
docker run --rm -v "$VOL":/data -v "$HERE/data":/src:ro alpine sh -c \
  'cp -r /src/. /data/ && chown -R 10001:10001 /data'
echo "seeded $VOL from $HERE/data"
