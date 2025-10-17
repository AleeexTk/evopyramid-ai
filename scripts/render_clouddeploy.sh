#!/usr/bin/env bash
set -euo pipefail

# Render Cloud Deploy manifests from templates using environment parameters.
# Required variables:
#   PROJECT_ID - target Google Cloud project id
# Optional variables:
#   REGION (default: us-central1)
#   STAGING_SERVICE (default: evopyramid-api-staging)
#   PRODUCTION_SERVICE (default: evopyramid-api)
#   OUTPUT_DIR (default: clouddeploy/rendered)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$ROOT_DIR/clouddeploy/templates"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/clouddeploy/rendered}"

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "[clouddeploy] PROJECT_ID must be set" >&2
  exit 1
fi

export ROOT_DIR
export TEMPLATE_DIR
export OUTPUT_DIR
export PROJECT_ID
export REGION="${REGION:-us-central1}"
export STAGING_SERVICE="${STAGING_SERVICE:-evopyramid-api-staging}"
export PRODUCTION_SERVICE="${PRODUCTION_SERVICE:-evopyramid-api}"

mkdir -p "$OUTPUT_DIR"

python - <<'PY'
import os
from pathlib import Path
from string import Template

template_dir = Path(os.environ["TEMPLATE_DIR"])
output_dir = Path(os.environ["OUTPUT_DIR"])

template = Template((template_dir / "delivery-pipeline.yaml.tpl").read_text())
rendered = template.safe_substitute(
    PROJECT_ID=os.environ["PROJECT_ID"],
    REGION=os.environ["REGION"],
    STAGING_SERVICE=os.environ["STAGING_SERVICE"],
    PRODUCTION_SERVICE=os.environ["PRODUCTION_SERVICE"],
)

output_path = output_dir / "delivery-pipeline.yaml"
output_path.write_text(rendered)
print(f"Rendered Cloud Deploy pipeline to {output_path}")
PY
