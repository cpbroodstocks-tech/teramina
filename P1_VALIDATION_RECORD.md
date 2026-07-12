# P1 Validation Record

Date: 2026-07-11

## Completed Locally

- Backend suite with coverage: 397 tests passed, 58% application statement coverage.
- Production-style `python manage.py check --deploy`: passed with `DEBUG=False`, explicit hosts/origins, JWT/Django secrets, Redis URLs, and a CI-style MongoDB URI.
- Frontend suite with coverage: 192 tests passed; 39.88% statements/lines, 63.86% branches, and 48.76% functions.
- CI coverage floors: backend 57%; frontend 39% statements/lines, 63% branches, and 48% functions.
- Backup/restore, alerting, rollback, secret-rotation, incident-ownership, and SLO procedures documented.

## Staging Blockers

- `gh auth status` reports the configured `cpbroodstocks-tech` token as invalid.
- GitHub API access is unavailable, so environment secrets and workflow dispatch cannot be inspected or executed.
- No usable staging SSH host alias is configured locally; `staging` resolves only as a literal hostname with the local user.
- No real Firebase staging session or seeded farmer credentials are available for authenticated browser smoke testing.

## Resume Commands

After restoring access:

```bash
gh auth login -h github.com
./scripts/check_deploy_readiness.sh staging
gh workflow run deploy.yml -f target=staging -f service=all
```

Then execute `MNEMON_BETA_RUNBOOK.md`, `GOOGLE_SHEETS_MANUAL_QA.md`, and `OPERATIONS_RUNBOOK.md`, attaching workflow URLs, timestamps, collection counts, health output, and rollback/restore evidence to this record.
