# P1 Validation Record

Updated: 2026-07-13

## Completed Locally

- Backend suite with coverage: 397 tests passed, 58% application statement coverage.
- Production-style `python manage.py check --deploy`: passed with `DEBUG=False`, explicit hosts/origins, JWT/Django secrets, Redis URLs, and a CI-style MongoDB URI.
- Frontend suite with coverage: 192 tests passed; 39.88% statements/lines, 63.86% branches, and 48.76% functions.
- CI coverage floors: backend 57%; frontend 39% statements/lines, 63% branches, and 48% functions.
- Backup/restore, alerting, rollback, secret-rotation, incident-ownership, and SLO procedures documented.

## Staging Blockers

- Staging diagnostics run `29215932803` reached the host and completed on 2026-07-13.
- Django, Redis, the Celery worker, Firebase credentials, MongoDB, and five seeded dashboard cycles were healthy; dashboard, economics, feeding, and water-quality checks returned 200.
- Celery Beat was restart-looping because Compose selected the relational `django_celery_beat` scheduler in a MongoEngine-only deployment. The Compose fix is pending deployment.
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` is registered in the GitHub staging environment but resolves empty. Google Sheets and storage cannot pass until a valid rotated credential is installed.
- Deployment now fails before modifying the server when critical backend secrets are empty.
- Backend deploy run `29216069360` verified that fail-closed behavior and stopped at preflight with only `GOOGLE_APPLICATION_CREDENTIALS_JSON` empty; no server write or container restart occurred.
- Frontend deploy run `29216633434` built and uploaded the production artifact, restarted staging, and passed its public health check. The rollback path was armed but was not failure-injected.
- No real Firebase staging session or seeded farmer credentials are available for authenticated browser smoke testing.
- Backup/restore, alert delivery, rollback, and credential-rotation drills still require staging operator access and isolated restore resources.

## Resume Commands

After installing the rotated Google credential and deploying the pending fixes:

```bash
./scripts/check_deploy_readiness.sh staging
gh workflow run deploy.yml -f target=staging -f service=all
```

Then execute `MNEMON_BETA_RUNBOOK.md`, `GOOGLE_SHEETS_MANUAL_QA.md`, and `OPERATIONS_RUNBOOK.md`, attaching workflow URLs, timestamps, collection counts, health output, and rollback/restore evidence to this record.
