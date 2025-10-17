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

export PROJECT_ID
export REGION="${REGION:-us-central1}"
export STAGING_SERVICE="${STAGING_SERVICE:-evopyramid-api-staging}"
export PRODUCTION_SERVICE="${PRODUCTION_SERVICE:-evopyramid-api}"

mkdir -p "$OUTPUT_DIR"

envsubst < "$TEMPLATE_DIR/delivery-pipeline.yaml.tpl" > "$OUTPUT_DIR/delivery-pipeline.yaml"

echo "Rendered Cloud Deploy pipeline to $OUTPUT_DIR/delivery-pipeline.yaml"
