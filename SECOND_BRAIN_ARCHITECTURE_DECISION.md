# Second Brain Architecture Decision

## Status

Accepted for the current beta branch.

## Decision

The current second-brain beta will continue on the existing Django Ninja + MongoEngine + MongoDB platform. `SECOND_BRAIN_DEV_PLAN.md` remains the strategic target architecture, while `MNEMON_DEV_PLAN.md`, `MNEMON_BETA_TODO.md`, and `MNEMON_BETA_RUNBOOK.md` are the active execution documents for the current branch.

`CYBERNETIC_PRODUCT_FRAMEWORK.md` is the product-level framework above these technical plans. Architecture decisions should support that framework: state, trajectory, margin, uncertainty, feedback, and risk-adjusted profit.

Postgres, TimescaleDB, pgvector, voice notes, offline daily log, and Temporal workflows are deferred until the beta path is validated with real farmer data.

## Rationale

- The MongoEngine Mnemon implementation is already close to beta readiness.
- Memory CRUD, graph observations, scoped retrieval, chat context, alert/task workflows, Today view, Memory review, and pond timeline are already implemented and tested in the current stack.
- Starting the data-platform migration now would mix product validation with infrastructure migration, increasing risk and making failures harder to diagnose.
- Real beta usage should inform whether MongoDB/local embedding retrieval is insufficient before introducing pgvector or TimescaleDB.

## Active Track

The active beta track is:

- Keep MongoEngine as the source of truth for second-brain memory.
- Keep flat memory and graph observations in sync.
- Use Celery + Redis for scheduled monitoring and pattern jobs.
- Use the existing chat and memory UI for farmer-facing beta feedback.
- Finish authenticated smoke testing with seeded farmer data.
- Refresh or open the `feature/second-brain-production-readiness` PR after beta checks pass.

## Deferred Tracks

The following tracks are intentionally out of scope for the current beta branch:

- Postgres canonical data model.
- TimescaleDB water-quality and observation hypertables.
- pgvector-backed retrieval.
- OpenAI Agents SDK migration.
- Temporal long-running workflows.
- Voice-note capture and transcription.
- Offline-first daily log and background sync.
- Native mobile application.
- Full graph visualization.

## Migration Gate

Revisit Postgres, TimescaleDB, and pgvector only after:

- Authenticated beta smoke tests pass with real Firebase session and seeded farm data.
- Mnemon eval gates pass for the beta answer set.
- Memory CRUD, correction, verification, deletion, and backfill are stable in staging.
- Pattern jobs run manually and through Celery Beat without unexpected duplicates.
- Product feedback shows MongoDB/local embedding retrieval is not enough, or reporting/audit requirements require relational storage.

## Documentation Ownership

- `CYBERNETIC_PRODUCT_FRAMEWORK.md`: product philosophy, feature contract, and decision standard.
- `SECOND_BRAIN_DEV_PLAN.md`: strategic architecture and long-term roadmap.
- `MNEMON_DEV_PLAN.md`: active MongoEngine Mnemon implementation plan.
- `MNEMON_BETA_TODO.md`: current beta checklist.
- `MNEMON_BETA_RUNBOOK.md`: rollout and smoke-test procedure.
- `SECOND_BRAIN_MIGRATION_NOTES.md`: MongoDB memory backfill and lifecycle notes before future vector work.
