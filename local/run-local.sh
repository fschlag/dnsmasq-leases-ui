#!/usr/bin/env bash
# Build image, run container with sample leases file mounted.
# Usage: ./local/run-local.sh [host_port]   (default 5000)
set -euo pipefail

PORT="${1:-5000}"
IMAGE="dnsmasq-leases-ui:local"
NAME="dnsmasq-leases-ui-local"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLE="$SCRIPT_DIR/dnsmasq.leases.sample"

if [[ ! -f "$SAMPLE" ]]; then
    echo "Missing $SAMPLE" >&2
    exit 1
fi

docker build -t "$IMAGE" "$REPO_ROOT"

docker rm -f "$NAME" >/dev/null 2>&1 || true

docker run --rm -it \
    --name "$NAME" \
    -p "${PORT}:5000" \
    -v "${SAMPLE}:/var/lib/misc/dnsmasq.leases:ro" \
    "$IMAGE"
