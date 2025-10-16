# EvoSync Notion Directive

> **Kairos Signal:** Unifies GitHub commits, EvoMemory snapshots, and Notion 3.0 AI agents into one living ledger of architectural change.

## Purpose

- Translate repository activity into structured knowledge inside Notion.
- Preserve the Kairos/Chronos narrative for every mutation of EvoPyramid.
- Allow Notion-native agents to collaborate with EvoRouter, Codex, and Trinity without breaking lineage boundaries.
- Sustain the EvoPyramid Canon by ensuring each change is contextualised before it is archived.

## Synchronization Flow

1. **GitHub → EvoRouter**
   - GitHub webhooks (`push`, `pull_request`, `release`) post signed payloads to `api/router.py`.
   - Payloads are normalised into `KairosEvent` JSON envelopes and queued for delivery.
2. **EvoRouter → EvoMemory Buffer**
   - Events are mirrored into `EvoMemory/KairosLog/` for provenance.
   - Trinity Observer compares commit timestamps against the last Notion reflection.
3. **EvoRouter → Notion API**
   - Authenticated call to `POST https://api.notion.com/v1/pages` writes an entry to the `EvoRepository Tracking` database.
   - Required fields: repository, module, commit hash, author, impact level, Kairos tier.
4. **Notion 3.0 AI Agents**
   - Resident agents (EvoSoul, Codex, Observer, FinArt) react to new rows via workflow automations.
   - Agents can trigger follow-up sync back to EvoRouter (for comments, annotations, or task creation).
5. **Notion → EvoRouter Feedback Loop**
   - Notion agents may emit follow-up webhooks (`/api/router.py#/notion_feedback`) when human annotations require GitHub issues or rituals.
   - Feedback events are written to `EvoMemory/Feedback/Notion/` and surfaced to Codex review.

## Agent Field Guide

| Agent | Tier | Mandate | Primary Notion Surface |
| --- | --- | --- | --- |
| **EvoSoul** | Syntonic | Maintain emotional & symbolic coherence of each row. | Docs, Ritual Journals |
| **Codex** | Structural | Analyse diffs, highlight impact, draft countermeasures. | Engineering Hub |
| **Observer** | Cognitive | Cross-check Chronos/Kairos parity and escalate missing reflections. | Monitoring Board |
| **FinArt** | Creative | Run scenario simulations and create visual dashboards. | Timeline & Map Views |

Each agent attaches its resonance tag (`field_alignment`, `analysis`, `alert`, `vision`) which is mirrored back to EvoMemory for the Trinity Council.

## Data Schema

| Field | Description | Source |
| --- | --- | --- |
| `timestamp` | ISO8601 moment of the commit or release. | GitHub payload |
| `repo` | Name of the active repository. | GitHub payload |
| `module` | Affected subsystem path (e.g., `EvoCore/API`). | Codex diff parser |
| `action` | `create`, `update`, `delete`, or `release`. | GitHub event type |
| `hash` | Commit SHA or tag reference. | GitHub payload |
| `author` | Canonical author handle. | GitHub payload |
| `impact` | Architectural impact class (`architecture`, `framework`, `ritual`, etc.). | Codex heuristics |
| `kairos_level` | Integer resonance level (1-5). | Trinity Observer |
| `synced` | Boolean showing Notion acknowledgement. | Notion response |
| `agent_tags` | Ordered list of Notion agent resonance markers. | Notion AI agents |
| `lineage` | Reference to `EVO_ARCH_MAP.yaml` branch. | Codex lineage mapper |

## Security & Authenticity

- Every packet is sealed with **EvoSeal AES-256** signatures before leaving EvoRouter.
- Notion API tokens are stored in the `EvoAuth v3` vault and rotated quarterly.
- Row-level permissions in Notion ensure only sanctioned agents manipulate Kairos records.
- Failed deliveries raise an EvoRouter alert and queue a replay job.
- Each mirrored row stores an `evo_hash` signature so the Trinity Observer can prove provenance when auditing Notion-native edits.

## Visualization Rituals

- **Timeline View:** Chronicles evolution across Kairos levels.
- **Map View:** Plots geographic context when location metadata is present.
- **Cohesion Dashboard:** Aggregates commit resonance scores against Trinity coherence metrics.
- **Kairos Compass:** Four-quadrant board mapping `impact × kairos_level` for daily Trinity reflections.
- **EvoDashboard Export Loop:** GitHub Actions запускает `scripts/export_dashboards.py`, чтобы сформировать `EvoDashboard/*.json` артефакты (Compass, Cohesion, Timeline/Map) и закрепить визуализации Kairos ↔ Logos в CI.【F:scripts/export_dashboards.py†L1-L11】【F:scripts/export_dashboards.py†L368-L380】【F:.github/workflows/ci.yml†L33-L50】

## Operational Guidelines

- Define the directive inside Notion using the embedded YAML block:

```yaml
evo_directive:
  name: "EvoSync Notion Directive"
  source: "GitHub → EvoRouter → Notion"
  track: ["repo", "module", "commit", "timestamp", "author", "impact", "kairos_level", "agent_tags"]
  reflect: "EvoMemory + KairosLog + Notion Feedback Buffer"
  visualize: ["Notion Timeline", "Notion Map View", "Kairos Compass"]
  security: "EvoSeal AES256"
```

- Each synced event must reference its parent lineage in `EVO_ARCH_MAP.yaml`.
- Trinity Observer audits the Notion ledger daily; discrepancies trigger Codex review tasks.
- Observer or Codex agents can append contextual commentary directly within the Notion row — these annotations are mirrored back to EvoMemory during the next sync loop.
- EvoRouter stores transmission metrics (`latency_ms`, `retries`) in `logs/trinity_metrics.log` for long-term Kairos analysis.

## Implementation Checklist

1. Register GitHub webhook secrets in EvoRouter (`api/config/notion.yaml`).
2. Provision Notion integration with database-level permissions and capture the integration ID in EvoAuth v3.
3. Extend `api/router.py` with the `/notion_feedback` endpoint to accept agent feedback payloads.
4. Configure EvoRouter retry queue (Redis recommended; fallback to SQLite queue for offline environments).
5. Run smoke tests (`pytest tests/api/test_notion_bridge.py`) before enabling the directive in production.

## Observability Metrics

- **Sync Lag:** `Trinity Observer` reports average delay between GitHub commit and Notion row creation.
- **Replay Count:** Number of Notion delivery retries executed per 24h window.
- **Agent Coverage:** Percentage of rows annotated by at least one Notion AI agent.
- **Lineage Integrity:** Ratio of rows with valid `lineage` references.

## Next Evolution Steps

1. Wire automated regression tests for the EvoRouter → Notion bridge to validate schema drift.
2. Extend `api/router.py` with a retryable task queue (Redis or local persistent queue) to guard against transient Notion outages.
3. Surface Notion acknowledgement metrics alongside Codex CI results in `logs/trinity_metrics.log`.
4. Протестировать экспорт EvoDashboard на аномальных `KairosEvent` (нулевые и отрицательные `impact`, отсутствующие `agent_tags`), чтобы гарантировать устойчивость визуализаций.
5. Prototype a reverse sync where Notion decisions (e.g., approved rituals) spawn GitHub issues via EvoRouter.
6. Formalise agent training prompts inside Notion's AI Workflow library so they inherit EvoPyramid Canon language.
