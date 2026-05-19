# Mnemon Beta Readiness Todo

## Goal

Move Mnemon from MVP-complete to beta-ready without mixing in voice notes, daily log, or Postgres/pgvector migration work.

## Todo

- [x] Keep the pushed MongoEngine Mnemon MVP isolated from experimental local work.
- [x] Add a runnable Mnemon eval command for CI/manual answer-set checks.
- [x] Add focused tests for the eval command.
- [ ] Create an authenticated smoke-test checklist for farmer chat and memory review.
- [ ] Add beta rollout notes for the memory backfill command and Celery pattern jobs.
- [ ] Decide whether low-confidence memory review needs an internal admin UI or whether the farmer-facing review tab is enough for beta.
- [ ] After beta checks pass, open/refresh the PR for `feature/second-brain-production-readiness`.

## Completed Execution Slice

1. [x] Add `run_mnemon_evals` management command.
2. [x] Support JSON and JSONL answer files.
3. [x] Print a compact pass/fail summary and fail non-zero when quality gates fail.
4. [x] Add tests covering pass and fail behavior.
5. [x] Run focused backend checks.

## Next Execution Slice

1. Create an authenticated smoke-test checklist for farmer chat and memory review.
2. Add rollout notes for `backfill_agent_memory_graph --apply`.
3. Add rollout notes for enabling periodic pattern jobs.
4. Decide whether to keep the experimental voice/daily-log work in this branch or move it to a separate branch.
