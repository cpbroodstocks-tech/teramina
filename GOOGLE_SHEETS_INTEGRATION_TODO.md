# Google Sheets Integration TODO

## 1. Sync Job Contract

- Add a first-class sync job ID to manual sync and confirmed sync responses.
- Store the active sync job ID on the integration while a job is running.
- Return the active/latest sync job ID from status.
- Keep status values explicit: `pending`, `queued`, `syncing`, `ok`, `partial`, `error`.
- Make stale preview failures visible as a normal sync failure with a clear message.

## 2. Endpoint Test Coverage

- Test `/sheets/manual-sync` for unauthorized, missing integration, lock contention, and queued job payload.
- Test `/sheets/preview-sync` for dry-run payload, preview fingerprint storage, and validation summary.
- Test `/sheets/confirm-sync` for expired preview, unauthorized preview, stale fingerprint handoff, and lock contention.
- Test `/sheets/sync-log` ordering and missing-log behavior.

## 3. Sync Log Quality

- Store per-tab errors in `SheetSyncLog`, not only summary counts.
- Store source fingerprint and source spreadsheet ID on each sync log.
- Store duration and rows-per-second metrics for operational debugging.
- Preserve rejected-row warnings separately from hard errors.

## 4. Frontend Status UX

- Show the active sync job ID/state when a sync is queued or running.
- Poll the current job or latest sync log instead of only polling integration status.
- Surface sync-log load errors explicitly.
- Add a stale-preview recovery path that lets the user rerun preview in one click.

## 5. Stable Row Identity

- Add hidden/import-managed row IDs to generated templates.
- Use row IDs as idempotency keys before falling back to natural keys.
- Backfill row IDs when syncing older templates.
- Preserve compatibility with manually created sheets that do not have row IDs.

## 6. Deletion And Import Modes

- Add import modes: `valid_rows_only`, `strict`, and later `mirror_sheet`.
- Keep `valid_rows_only` as the default to avoid accidental destructive edits.
- In `strict`, block the whole import if any row has hard errors.
- In `mirror_sheet`, allow explicit delete markers or row-ID based deletions.

## 7. Sheet-Side Feedback

- Add status/error columns to template tabs.
- Write validation feedback back to the relevant sheet row after sync.
- Include tab, row, field, severity, and actionable reason.
- Avoid overwriting farmer-entered data columns.

## 8. Access And Reliability

- Add an access health check to status so revoked access is visible before sync.
- Add bounded retries for transient Google API failures.
- Do not retry validation/data-shape failures.
- Rate-limit manual sync per cycle/user.
- Expose background sync enablement and frequency controls per cycle.

## 9. Observability

- Log sync job ID, cycle ID, spreadsheet ID, status, duration, and per-tab counts.
- Track lock contention and stale-preview failures.
- Add alertable error categories for Google auth, Google quota, validation, and database write failures.
- Add metrics hooks around Google API calls and DB writes.
