# Cloud Deploy pipeline manifest for EvoPyramid API
# Render this template with scripts/render_clouddeploy.sh before applying.
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata:
  name: evopyramid-api
  labels:
    evo.tier: structural
    evo.pace: cloud
    evo.owner: evopyramid
description: |
  Progressive delivery pipeline orchestrating EvoPyramid API promotions on Cloud Run
  while following the PACE ritual (Plan → Apply → Check → Elevate).
serialPipeline:
  stages:
    - targetId: evopyramid-staging
      profiles:
        - staging
    - targetId: evopyramid-production
      profiles:
        - production
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: evopyramid-staging
  labels:
    evo.env: staging
description: |
  Staging Cloud Run surface for rehearsing EvoPyramid API releases before Chronos
  elevation into production.
run:
  location: projects/${PROJECT_ID}/locations/${REGION}
  service: ${STAGING_SERVICE}
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: evopyramid-production
  labels:
    evo.env: production
description: |
  Production Cloud Run surface for EvoPyramid API once harmony has been verified
  within staging.
run:
  location: projects/${PROJECT_ID}/locations/${REGION}
  service: ${PRODUCTION_SERVICE}
