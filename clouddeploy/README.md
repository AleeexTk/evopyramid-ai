# EvoPyramid Cloud Deploy Harness

This directory houses the infrastructure artifacts that turn the Google Cloud deployment guide
into an executable delivery pipeline.

## Components

- `templates/delivery-pipeline.yaml.tpl` — template for the Cloud Deploy delivery pipeline and Cloud Run targets.
- `rendered/` — output directory for rendered manifests (git-kept empty).
- `../skaffold.yaml` — Skaffold config consumed by Cloud Deploy when rendering releases.
- `../cloudbuild.yaml` — Cloud Build definition that builds the API image and creates releases.
- `../scripts/render_clouddeploy.sh` — helper that renders the pipeline template using environment variables (project, region, Cloud Run service names).
- `../scripts/trigger_cloud_build.sh` — wraps `gcloud builds submit` with EvoPyramid defaults so the Cloud Build → Cloud Deploy promotion path can be exercised on demand.
- `../scripts/render_clouddeploy.sh` — helper that renders the pipeline template using environment variables.

## Usage (PACE Elevate)

```bash
PROJECT_ID=your-project \
REGION=us-central1 \
STAGING_SERVICE=evopyramid-api-staging \
PRODUCTION_SERVICE=evopyramid-api \
scripts/render_clouddeploy.sh
PROJECT_ID=your-project REGION=us-central1 scripts/render_clouddeploy.sh

gcloud deploy apply \
    --file clouddeploy/rendered/delivery-pipeline.yaml \
    --region=${REGION} \
    --project=${PROJECT_ID}

PROJECT_ID=${PROJECT_ID} \
REGION=${REGION} \
STAGING_SERVICE=${STAGING_SERVICE} \
PRODUCTION_SERVICE=${PRODUCTION_SERVICE} \
scripts/trigger_cloud_build.sh
```

Cloud Build triggers pointed at `cloudbuild.yaml` now render and apply the delivery pipeline automatically before creating a release, keeping manual invocations optional. The trigger script mirrors the same behaviour locally, ensuring production substitutions are validated before promoting a change.

Custom Cloud Build substitutions `_STAGING_SERVICE` and `_PRODUCTION_SERVICE` mirror the environment variables, enabling per-environment overrides without editing the repository files.
gcloud deploy releases create evopyramid-api-$(date +%Y%m%d%H%M%S) \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --delivery-pipeline=evopyramid-api \
    --skaffold-file=skaffold.yaml \
    --images=evopyramid-api=${REGION}-docker.pkg.dev/${PROJECT_ID}/evopyramid-repo/evopyramid-api:$(git rev-parse HEAD)
```

Cloud Build triggers pointed at `cloudbuild.yaml` now render and apply the delivery pipeline automatically before creating a release, keeping manual invocations optional.

Custom Cloud Build substitutions `_STAGING_SERVICE` and `_PRODUCTION_SERVICE` mirror the environment variables, enabling per-environment overrides without editing the repository files.
Cloud Build triggers pointed at `cloudbuild.yaml` will execute the same flow automatically.
