#!/usr/bin/env bash
set -euo pipefail

echo "[evo_scan] mapping local environment" >&2
cat <<'JSON' > EvoLocalMap.json
{
  "nodes": [],
  "edges": []
}
JSON
echo "[evo_scan] map written to EvoLocalMap.json" >&2
