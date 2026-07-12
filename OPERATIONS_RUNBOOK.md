# Teramina Operations Runbook

## Service Health

Expected components are frontend nginx, Django API, MongoDB, Redis, Celery worker, and Celery beat.

```bash
curl --fail --silent --show-error http://<host>:8000/health/
curl --fail --silent --show-error http://<host>/
docker compose ps
docker compose logs --since=15m web celery_worker celery_beat redis
docker compose exec web celery -A teramina inspect ping
docker compose exec web celery -A teramina inspect active
docker compose exec web celery -A teramina inspect reserved
docker compose exec web celery -A teramina inspect scheduled
```

## Backup and Restore Drill

Create a timestamped encrypted-at-rest backup using credentials scoped to the intended environment:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "backups/${STAMP}"
mongodump --uri "$MONGODB_URI" --archive="backups/${STAMP}/teramina.archive" --gzip
shasum -a 256 "backups/${STAMP}/teramina.archive" > "backups/${STAMP}/SHA256SUMS"
```

Restore into an isolated drill database, never over the source database:

```bash
shasum -a 256 -c "backups/${STAMP}/SHA256SUMS"
mongorestore --uri "$MONGODB_RESTORE_URI" --archive="backups/${STAMP}/teramina.archive" --gzip --drop
```

Pass criteria:

- checksum and restore succeed;
- farm, pond, cycle, user, memory, sheet-integration, and report collection counts match;
- the application starts against the restored database and `/health/` succeeds;
- timestamp, backup size, restore duration, counts, operator, and result are recorded.

## Alerting

Required alerts:

- API health fails twice over two minutes;
- server error rate exceeds 2% for five minutes;
- p95 API latency exceeds 1.5 seconds for ten minutes;
- MongoDB or Redis connectivity fails;
- Celery worker has no heartbeat for two minutes;
- oldest queued job exceeds five minutes;
- scheduled job fails or beat has no heartbeat for five minutes;
- disk usage exceeds 80%;
- backup is older than 24 hours or the latest restore drill failed.

Every alert must identify an owner, severity, environment, log/dashboard link, and first-response action.

## Rollback Drill

1. Record the current healthy SHA and image IDs.
2. Deploy a failing health-check-only staging revision that cannot modify data.
3. Confirm the workflow restores the previous SHA/artifact.
4. Confirm frontend/backend health and worker/beat revision.
5. Record detection time, rollback time, and manual intervention.

Never use a schema or destructive-data change for this drill.

## Secret Rotation

1. Create a replacement at the provider.
2. Update the target GitHub environment secret.
3. Deploy and verify health plus the affected integration.
4. Revoke the old secret after verification.
5. Confirm the old secret fails and record date and owner.

Rotate MongoDB, Django/JWT, Firebase, Google Cloud, OpenAI, Anthropic, Pinecone, and Teramina credentials independently.

## Incident Ownership

- Incident commander: on-call engineering lead.
- Backend/data owner: Django, MongoDB, Redis, Celery, and integrations.
- Frontend owner: nginx, assets, Firebase client auth, and browser telemetry.
- Product/data owner: farm calculations, reports, Mnemon answers, and customer communication.

For severity 1 incidents, stop deployments, preserve logs, maintain a shared timeline, and update stakeholders at least every 30 minutes.
