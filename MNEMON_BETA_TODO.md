# Mnemon Beta Readiness Todo

## Goal

Move Mnemon from MVP-complete to beta-ready without mixing in voice notes, daily log, or Postgres/pgvector migration work.

## Todo

- [x] Keep the pushed MongoEngine Mnemon MVP isolated from experimental local work.
- [x] Add a runnable Mnemon eval command for CI/manual answer-set checks.
- [x] Add focused tests for the eval command.
- [x] Create an authenticated smoke-test checklist for farmer chat and memory review.
- [x] Add beta rollout notes for the memory backfill command and Celery pattern jobs.
- [x] Decide whether low-confidence memory review needs an internal admin UI or whether the farmer-facing review tab is enough for beta.
- [ ] After beta checks pass, open/refresh the PR for `feature/second-brain-production-readiness`.

## Completed Execution Slice

1. [x] Add `run_mnemon_evals` management command.
2. [x] Support JSON and JSONL answer files.
3. [x] Print a compact pass/fail summary and fail non-zero when quality gates fail.
4. [x] Add tests covering pass and fail behavior.
5. [x] Run focused backend checks.

## Next Execution Slice

1. [x] Create an authenticated smoke-test checklist for farmer chat and memory review.
2. [x] Add rollout notes for `backfill_agent_memory_graph --apply`.
3. [x] Add rollout notes for enabling periodic pattern jobs.
4. [x] Decide whether low-confidence review needs internal admin UI for beta.
5. [ ] Move or park experimental voice/daily-log/Postgres work before PR refresh.
6. [ ] Run the authenticated smoke checklist with real Firebase session and seeded farmer data.
7. [ ] Open/refresh the PR for `feature/second-brain-production-readiness`.

## Beta Readiness Decision

For beta, the farmer-facing Memory review page is enough for low-confidence memory review. An internal admin queue should wait until beta usage shows real support-team review volume or false-positive pattern memory pressure.

Detailed runbook: `MNEMON_BETA_RUNBOOK.md`.
