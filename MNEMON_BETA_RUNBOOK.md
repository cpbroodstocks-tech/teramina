# Teramina Mnemon Beta Runbook

## Goal

Use this runbook to move the MongoEngine Mnemon MVP into beta without mixing in the future Postgres/pgvector, voice notes, or daily log tracks.

## Beta Scope

Included:

- Context-aware assistant chat payloads with `farm_id`, `pond_id`, `cycle_id`, and `page_context`.
- Farmer-confirmed memory creation from chat and the Memory page.
- Memory review, verification, and delete flow.
- Per-pond memory/history panel.
- Graph memory documents backed by MongoEngine.
- Periodic pattern detection through Celery Beat.
- Deterministic Mnemon answer quality gates.

Deferred:

- Full graph visualization.
- Autonomous unconfirmed memory writes.
- Postgres/pgvector migration.
- Voice-note capture and daily log workflows.
- Native mobile surfaces.

## Authenticated Smoke-Test Checklist

Run this against a seeded farmer account with at least one farm, pond, active cycle, water-quality data, feed data, and one existing memory.

### Backend

1. Start backend dependencies.
   - MongoDB must point at the intended staging database.
   - Redis must be available if Celery tasks are being tested.
2. Start Django.
   - `python manage.py runserver`
3. Confirm API boot.
   - Open `/api/docs`.
   - Confirm `/agent/chat`, `/agent/memories`, and `/agent/memory-graph` are present.
4. Run backend checks.
   - `python manage.py check`
   - `python -m pytest tests/test_agent_memory.py tests/test_agent_monitoring.py tests/test_mnemon_eval.py -q`

### Frontend

1. Start the Vite app.
   - `yarn dev`
2. Log in with the seeded farmer account.
3. Open a pond or active cycle page.
4. Open assistant chat and ask: `What happened last time DO was low?`
5. Confirm the network request sends:
   - `message`
   - `session_id`
   - `farm_id`
   - `pond_id`
   - `cycle_id`
   - `page_context.route`
   - `page_context.page_type`
6. Confirm the answer uses the current farm/pond context and does not invent missing numbers.
7. Send a direct memory candidate, for example: `Remember that Pond B gets low DO after heavy rain.`
8. Confirm the assistant shows the confirmation prompt before saving.
9. Click the save/remember action.
10. Confirm the success chip says `Remembered: ...`.

### Memory Review

1. Open the Memory page.
2. Filter by the active farm.
3. Confirm the saved memory appears with type, source, confidence, tags, and created date.
4. Verify a low-confidence or unverified memory.
5. Delete a test memory.
6. Refresh the page and confirm the deleted memory and its graph observation no longer appear.
7. Open a pond detail surface with the pond history panel.
8. Confirm the panel groups prior items into recurring issues, what worked before, harvest outcomes, and notes.

### Pattern Jobs

1. Run the pattern task on staging data through Celery or Django shell.
2. Confirm duplicate pattern memories are not created on a second run.
3. Confirm created pattern memories have:
   - `memory_type=event`
   - `source=system_observation`
   - `is_verified=True`
   - `pattern` tag
   - `risk:<level>` tag
4. Ask chat a pond-specific question and confirm pattern memories are retrieved only for the scoped farm/pond.

### Evals

1. Prepare a JSON or JSONL answer file with generated answers for the standard Mnemon questions.
2. Run:
   - `python manage.py run_mnemon_evals --answers path/to/answers.json`
3. Treat any failed gate as a beta blocker unless the answer set is intentionally incomplete.

## Backfill Rollout

### Conversation Session Index Migration

The production-ready chat session key is now `(user_id, session_id)`, not a globally
unique `session_id`. Before deploying to an existing MongoDB database:

1. Inspect `agent_conversations` for duplicate `(user_id, session_id)` pairs.
2. Drop the old global unique `session_id` index if it exists.
3. Create the compound unique index:
   - `db.agent_conversations.createIndex({ user_id: 1, session_id: 1 }, { unique: true })`
4. Keep existing documents unchanged unless duplicate pairs are found for the same user.

This prevents one farmer from reusing another farmer's client-supplied `session_id`.

### Memory Graph Backfill

The command is dry-run by default:

```bash
python manage.py backfill_agent_memory_graph
```

Recommended rollout:

1. Run a global dry-run and save the counts.
2. Run a farm-scoped dry-run for one known seeded farm:
   - `python manage.py backfill_agent_memory_graph --farm-id <farm_id>`
3. Review counts:
   - `memories_scanned`
   - `observations_created`
   - `observations_linked`
   - `memories_normalized`
   - `observations_normalized`
   - `duplicate_legacy_observations`
4. If counts are expected, apply to that farm:
   - `python manage.py backfill_agent_memory_graph --farm-id <farm_id> --apply`
5. Smoke-test Memory page and chat retrieval for that farm.
6. Apply globally only after the farm-scoped check passes:
   - `python manage.py backfill_agent_memory_graph --apply`
7. Re-run the dry-run. Expected result: no new observations needed and no unexpected duplicate count growth.

Rollback posture:

- `agent_memories` remains the source of truth for farmer-visible memories.
- `memory_observations` and `memory_embeddings` can be regenerated from `agent_memories`.
- If retrieval behaves incorrectly, disable semantic retrieval first and keep CRUD available.

## Celery Pattern Job Rollout

The committed schedule includes `detect-all-patterns` every 24 hours through `CELERY_BEAT_SCHEDULE`.
By default production uses Celery's persistent scheduler so Mnemon does not require Postgres just to run beat.
Set `CELERY_BEAT_SCHEDULER=django_celery_beat.schedulers:DatabaseScheduler` only if a Django relational database
and `django_celery_beat` migrations are deployed.

Required services:

- Django app with the Mnemon code deployed.
- Redis or configured `CELERY_BROKER_URL`.
- Celery worker:
  - `celery -A teramina worker --loglevel=info --concurrency=2`
- Celery beat:
  - `celery -A teramina beat --loglevel=info`

Beta rollout:

1. Enable worker first, with beat disabled.
2. Run one manual task invocation in staging.
3. Inspect logs for detector counts and errors.
4. Inspect Memory page for pattern memories.
5. Enable beat after the manual run is clean.
6. Watch the first scheduled run and confirm detector counts are stable.

Operational guardrails:

- Pattern jobs should be idempotent by pattern tag and cycle context.
- Created memories must remain scoped to the farm, pond, and cycle that produced the pattern.
- Pattern memories are system observations, not farmer preferences.
- Live cycle data still takes priority over old pattern memory in chat answers.

## Low-Confidence Review Decision

For beta, the farmer-facing Memory review page is enough.

Rationale:

- It already exposes unverified and low-confidence memories through review-oriented chips and actions.
- Beta scope favors farmer correction over an internal admin workflow.
- Internal admin UI should wait until there is real review volume or support-team ownership.

Add an internal admin queue later if:

- Farmers leave many unreviewed memories unresolved.
- Support needs cross-farm moderation.
- Pattern jobs create too many false positives.
- Compliance requires operator sign-off before memory affects recommendations.

## Beta Exit Criteria

- Authenticated smoke checklist passes for at least one seeded farmer.
- Backfill dry-run and apply pass without unexpected duplicate growth.
- Celery pattern jobs run once manually and once from beat without errors.
- `run_mnemon_evals` passes on the beta answer set.
- No experimental voice, daily log, or Postgres/pgvector files are included in the beta PR.
