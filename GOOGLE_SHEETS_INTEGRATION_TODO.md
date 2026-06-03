# Google Sheets Integration Finish TODO

## Goal

Finish the Google Sheets hardening track and keep this document accurate as the status artifact.

The original TODO was stale: several listed items are already implemented. This file now separates completed work, remaining work, and deferred decisions.

## Current Status

### Done

- [x] Manual and confirmed sync responses return a first-class `sync_id`.
- [x] `SheetIntegration` stores `active_sync_id` while a sync is queued or running.
- [x] Status returns `active_sync_id`, `last_sync_id`, explicit sync state, tab summaries, and access check fields.
- [x] Status values now include `pending`, `queued`, `syncing`, `ok`, `partial`, and `error`.
- [x] Stale preview fingerprint mismatch is surfaced as a normal sync error.
- [x] Endpoint tests cover manual sync, preview sync, confirm sync, sync log behavior, stale fingerprints, ownership, lock contention, and queued payloads.
- [x] `SheetSyncLog` stores per-tab summaries, per-tab errors, source spreadsheet ID, source fingerprint, duration, and rejected rows.
- [x] Frontend shows queued/running state, sync IDs, sync log load errors, stale-preview recovery, tab summaries, warnings, and errors.
- [x] Generated templates include import-managed row IDs, delete markers, and import status/message columns.
- [x] Sync backfills missing row IDs for existing generated templates.
- [x] Row IDs are used as idempotency keys before fallback natural keys.
- [x] Delete markers work for supported tabs without requiring a destructive mirror mode.
- [x] `valid_rows_only` remains the default import mode.
- [x] `strict` mode blocks import when hard validation errors are present.
- [x] Sheet-side validation feedback is written to import status/message columns.
- [x] Manual sync is rate-limited per cycle/user.
- [x] Transient Google API calls use bounded retries.
- [x] Optional status access health check exists behind `SHEETS_STATUS_ACCESS_CHECK=true`.
- [x] `SheetSyncLog`, `/sheets/sync-log`, status payloads, and frontend display include `rows_per_second`.
- [x] Sync-level and tab-level errors include `error_category`.
- [x] Error categories cover `google_auth`, `google_quota`, `google_transient`, `validation`, `database_write`, `lock_contention`, `stale_preview`, and `unknown`.
- [x] Frontend sync-log queries are sync-ID aware while preserving latest-log fallback.
- [x] Warning-only preview rows are no longer counted as hard errors.

## Finish TODO

### 1. Close Sync Log Observability Gaps

- [x] Add `rows_per_second` to `SheetSyncLog`, `/sheets/sync-log`, status payloads, and frontend display.
- [x] Add an `error_category` field for sync-level and tab-level errors.
- [x] Classify at least these categories: `google_auth`, `google_quota`, `google_transient`, `validation`, `database_write`, `lock_contention`, `stale_preview`, and `unknown`.
- [x] Add tests proving stale-preview failures and lock contention are categorized.
- [x] Keep rejected-row warnings separate from hard errors in API payloads and frontend copy.

### 2. Make Polling Job-Aware

- [x] Use `/sheets/sync-log?sync_id=...` so the existing endpoint remains backwards compatible.
- [x] Query the active sync ID or latest sync log while retaining latest-log fallback.
- [x] Keep integration-status polling as the compatibility fallback for older integrations.
- [x] Add frontend tests for active-sync log lookup and existing terminal-state behavior.

### 3. Resolve Import Mode Scope

- [x] Defer `mirror_sheet` for beta.
- [x] Document delete markers as the beta deletion path.
- [ ] Add manual QA for row-ID update, row-ID delete, natural-key fallback, and strict-mode rejection.

### 4. Harden Sheet-Side Feedback

- [ ] Verify with a real Google Sheet that import status/message columns are updated for hard errors, warnings, and successful rows.
- [ ] Confirm feedback writes do not overwrite farmer-entered data columns.
- [x] Add regression coverage for warning-only preview behavior versus hard-error behavior.
- [x] Update `GOOGLE_SHEETS_MANUAL_QA.md` with the final feedback verification steps.

### 5. Finish Access And Background Sync Controls

- [ ] Decide whether `SHEETS_STATUS_ACCESS_CHECK=true` should be enabled in staging and production.
- [x] Add user-facing copy for revoked or inaccessible spreadsheet states.
- [x] Keep global 30-minute sync as the beta decision; per-cycle controls are deferred.

### 6. Add Production Observability Hooks

- [x] Persist sync ID, cycle ID, spreadsheet ID, status, duration, rows-per-second, per-tab counts, and error category in sync logs.
- [x] Emit the same operational fields in worker logs without raw row contents.
- [ ] Add metrics hooks around Google API reads/writes and database writes.
- [ ] Add alert thresholds for repeated auth failures, quota failures, stale-preview failures, and database write failures.
- [ ] Ensure logs never include raw sheet row contents beyond controlled rejected-row diagnostics.

### 7. Final Verification

- [x] Run backend focused tests:

```bash
cd core-be-teramina-main
python -m pytest -q tests/test_google_sheets.py
```

- [x] Run frontend focused tests:

```bash
cd fe-teramina-main
yarn test src/tests/components/google-sheets.test.tsx
```

- [x] Run full production-bound gates before merge:

```bash
cd fe-teramina-main && yarn lint && yarn typecheck && yarn test && yarn build
cd ../core-be-teramina-main && python -m pytest -q && python manage.py check --deploy
```

- [ ] Complete `GOOGLE_SHEETS_MANUAL_QA.md` against a real spreadsheet with seeded cycle data.
- [ ] Update this file after verification so no completed item remains listed as open.

## Deferred Unless Product Scope Changes

- [ ] `mirror_sheet` destructive import mode.
- [ ] Per-row writeback for every successful imported row, if the current success/error column behavior is enough for beta.
- [ ] User-configurable background sync frequency, if global scheduled sync is accepted for beta.
- [ ] Backend tests for per-cycle background sync enablement/frequency, if that product decision changes.
