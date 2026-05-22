#!/usr/bin/env bash
# Convenience launcher for source checkouts. After `pip install -e .` you can
# just type `susurro` from anywhere instead of running this.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
exec "$PYTHON" -m susurro "$@"
