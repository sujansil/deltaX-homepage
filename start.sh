#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
printf 'Homepage: http://127.0.0.1:8080\nKeep this terminal open. Press Ctrl+C to stop the homepage only.\n'
exec python3 -m http.server 8080 --bind 127.0.0.1 --directory "${PROJECT_DIR}/dist"
