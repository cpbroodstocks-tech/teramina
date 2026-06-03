# Google Sheets Manual QA

Use this checklist against a real Google Sheet after backend, frontend, MongoDB, Redis/cache, and Celery worker are running.

## Setup

- Confirm `GOOGLE_APPLICATION_CREDENTIALS` points to the Sheets service account JSON.
- Open a cycle as the cycle owner.
- Create a Google Sheets template from the UI.
- Confirm the generated template has these system columns:
  - `Row ID`
  - `Delete?`
  - `Import Status`
  - `Import Message`
- Confirm the sheet is shared with the service account as editor.

## Preview And Import

- Add valid rows to `DAILY_LOG`, `ABW_SAMPLING`, `MORTALITY`, `COST`, and `HARVEST`.
- Add invalid rows:
  - bad date
  - missing required ABW
  - missing required harvest biomass
  - non-numeric mortality count
- Add warning rows:
  - non-numeric `COST` unit price with valid total
  - physiological warning values that are not hard failures
- Run `Review & Sync` with `Import valid rows`.
- Confirm preview shows valid, warning, and error counts correctly.
- Confirm warning-only rows increase the warning count but do not increase the error count.
- Confirm invalid rows are not imported and valid rows are queued.
- Confirm `Import Status` and `Import Message` are written beside rejected/warning rows.

## Strict Mode

- Set import mode to `Strict import`.
- Run `Review & Sync` while errors exist.
- Confirm preview is blocked and no sync is queued.
- Leave only warning rows in the sheet.
- Confirm strict preview allows import when no hard errors remain.
- Fix the invalid rows.
- Run `Review & Sync` in strict mode again.
- Confirm import queues and completes.

## Status, Polling, And Observability

- Start an import from `Review & Sync`.
- Confirm the UI shows `Queued` or `Syncing...` and a `Sync ID`.
- Confirm the sync log shown in the UI belongs to the active/latest sync ID, not an older import.
- Confirm completed imports show throughput as `rows/sec` when the backend returns it.
- Confirm tab summaries show inserted, updated, deleted, skipped, and issue counts.
- Create or simulate a stale preview.
- Confirm the UI shows error category `Stale preview`.
- Create or simulate a Google access failure.
- Confirm the UI shows error category `Google access`.

## Stale Preview

- Run `Review & Sync`.
- Before confirming, edit any source row in the sheet.
- Confirm the preview.
- Confirm sync fails with `Sheet changed since preview. Run preview-sync again.`
- Confirm the UI shows `Review Again`.
- Confirm the sync log/status payload classifies the failure as `stale_preview`.

## Manual Sync

- Click `Sync Now` with `Import valid rows`.
- Confirm status transitions through `queued`/`syncing` and ends in `Synced` or `Partial`.
- Confirm duplicate clicks within 60 seconds are rate-limited.
- Confirm concurrent sync attempts return `Sync already in progress`.
- Confirm lock-contention failures are classified as `lock_contention`.

## Access Health

- Enable `SHEETS_STATUS_ACCESS_CHECK=true` in a non-production environment.
- Confirm connected sheets show no access warning when the service account can read the sheet.
- Remove service-account access from the sheet.
- Refresh the app.
- Confirm the UI shows the spreadsheet access warning and the backend status payload includes `access_status=error`.
- Restore sheet access before continuing.

## Delete Marker

- Import a valid `COST` row and a valid `MORTALITY` row.
- Mark each row with `Y` in `Delete?`.
- Run `Review & Sync`.
- Confirm preview/sync summary counts deleted rows.
- Confirm the matching records are removed from app data.
- Confirm rows without matching existing records count as skipped, not deleted.

## Existing User Sheet Backfill

- Connect an older sheet that has data rows but blank `Row ID` cells.
- Run preview.
- Confirm blank `Row ID` cells are populated.
- Confirm user-entered data columns are unchanged.
- Run confirm sync.
- Confirm row identity remains stable after editing descriptions/notes.

## Regression Areas

- Feeding realization updates when `DAILY_LOG` feed fields change.
- Cost rows update when descriptions are corrected with stable `Row ID`.
- Harvest rows update with stable `Row ID`.
- Cycle water-quality data still validates hard failures and warnings.
- UI polling updates sync log and issue list after completion.
