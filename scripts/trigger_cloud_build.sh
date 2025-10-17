#!/usr/bin/env bash
set -euo pipefail

# Trigger the EvoPyramid Cloud Build pipeline with explicit substitutions so
# Cloud Deploy promotions can be exercised outside of repository triggers.
#
# Required environment variables:
#   PROJECT_ID      - Google Cloud project id that hosts Cloud Build / Cloud Deploy resources
# Optional environment variables:
#   REGION          - Google Cloud region for Artifact Registry, Cloud Deploy, Cloud Run (default: us-central1)
#   REPOSITORY      - Artifact Registry repository that stores the API image (default: evopyramid-repo)
#   DELIVERY_PIPELINE - Cloud Deploy delivery pipeline name (default: evopyramid-api)
#   STAGING_SERVICE   - Cloud Run staging service name (default: evopyramid-api-staging)
#   PRODUCTION_SERVICE - Cloud Run production service name (default: evopyramid-api)
#   IMAGE_TAG       - Tag to apply to the image / release (default: current git commit SHA or timestamp)
#   DRY_RUN         - When set to 1, prints the resolved gcloud command without executing it.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "[cloudbuild] PROJECT_ID must be provided" >&2
  exit 1
fi

REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-evopyramid-repo}"
DELIVERY_PIPELINE="${DELIVERY_PIPELINE:-evopyramid-api}"
STAGING_SERVICE="${STAGING_SERVICE:-evopyramid-api-staging}"
PRODUCTION_SERVICE="${PRODUCTION_SERVICE:-evopyramid-api}"

if [[ -n "${IMAGE_TAG:-}" ]]; then
  RESOLVED_TAG="$IMAGE_TAG"
else
  if git rev-parse --short HEAD >/dev/null 2>&1; then
    RESOLVED_TAG="$(git rev-parse --short HEAD)"
  else
    RESOLVED_TAG="manual-$(date +%Y%m%d%H%M%S)"
  fi
fi

if [[ "${DRY_RUN:-0}" != "0" ]]; then
  echo "[cloudbuild] DRY_RUN=1 — showing command only"
fi

GCLOUD_BIN="${GCLOUD_BIN:-gcloud}"

if ! command -v "$GCLOUD_BIN" >/dev/null 2>&1; then
if ! command -v gcloud >/dev/null 2>&1; then
  echo "[cloudbuild] gcloud CLI is required to trigger Cloud Build" >&2
  if [[ "${DRY_RUN:-0}" == "0" ]]; then
    exit 1
  fi
fi

if [[ "${DRY_RUN:-0}" == "0" ]]; then
  if ! "$GCLOUD_BIN" auth list --format='value(account)' | grep -q '.'; then
    echo "[cloudbuild] No active gcloud account detected. Run 'gcloud auth login' or 'gcloud auth activate-service-account' first." >&2
    exit 1
  fi
fi

GCLOUD_CMD=(
  "$GCLOUD_BIN" builds submit
GCLOUD_CMD=(
  gcloud builds submit
  "--project=${PROJECT_ID}"
  "--config=cloudbuild.yaml"
  "--substitutions=_REGION=${REGION},_REPOSITORY=${REPOSITORY},_DELIVERY_PIPELINE=${DELIVERY_PIPELINE},_STAGING_SERVICE=${STAGING_SERVICE},_PRODUCTION_SERVICE=${PRODUCTION_SERVICE},COMMIT_SHA=${RESOLVED_TAG}"
  .
)

echo "[cloudbuild] Triggering build with tag ${RESOLVED_TAG} in project ${PROJECT_ID}"
echo "[cloudbuild] Region: ${REGION}, Repo: ${REPOSITORY}, Pipeline: ${DELIVERY_PIPELINE}"

echo "${GCLOUD_CMD[@]}"

if [[ "${DRY_RUN:-0}" != "0" ]]; then
  exit 0
fi

"${GCLOUD_CMD[@]}"
