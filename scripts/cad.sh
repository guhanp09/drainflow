#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker run --rm --memory=4g --cpus=2 -v "$root:/work" "${CAD_IMAGE:-drainflow-cad}" scripts/export_cad.py
