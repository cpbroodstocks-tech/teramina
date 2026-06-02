# Deployment Checklist

This repository deploys two services:

- `core-be-teramina-main`: Django API, Celery worker, Celery beat, Redis
- `fe-teramina-main`: Vite static frontend served by nginx

## Active GitHub Workflows

Active workflows must live under the repository root `.github/workflows/` directory.

- `.github/workflows/ci.yml` - CI for pull requests and `main` pushes; also supports manual dispatch.
- `.github/workflows/deploy.yml` - SSH/Docker deployment for backend, frontend, or both.

The old sub-project workflow locations under `core-be-teramina-main/.github/` and `fe-teramina-main/.github/` are not active in GitHub Actions for this monorepo layout.

## Deployment Modes

Use `Deploy` from GitHub Actions for staging:

1. Select `Run workflow`.
2. Set `target` to `staging`.
3. Set `service` to `all`, `backend`, or `frontend`.
4. Use `run_commercial_seed` only after confirming the target MongoDB is the intended staging database.
5. Use `reindex_advisory_sources` after content/report data exists on staging.

Production deployment remains tag-driven:

```bash
git tag production-YYYYMMDD-N
git push origin production-YYYYMMDD-N
```

Before running a deployment, verify GitHub environment readiness:

```bash
./scripts/check_deploy_readiness.sh staging
./scripts/check_deploy_readiness.sh production
```

## Required Backend GitHub Secrets

Set these secrets in GitHub Actions environments, at minimum for `staging` before staging deploys and `production` before production deploys:

- `SSH_PRIVATE_KEY`
- `SSH_KNOWN_HOSTS`
- `SSH_USER`
- `SSH_HOST`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `JWT_SECRET_KEY`
- `MONGODB_URI`
- `FIREBASE_CREDENTIALS_JSON`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TERAMINA_LLM_API`
- `TERAMINA_API_KEY`
- `SUMMARY_MODEL`
- `PINECONE_API_KEY`
- `PINECONE_INDEX`
- `GS_BUCKET_NAME`
- `GS_PROJECT_ID`
- `GS_VDB_BUCKET_NAME`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CACHE_REDIS_URL`
- `SENTRY_DSN`
- `DATA_UPLOAD_MAX_MB`
- `FILE_UPLOAD_MAX_MB`

`DJANGO_DEBUG` is forced to `False` by the workflow.

## Required Frontend GitHub Secrets

Set these secrets in the same GitHub Actions environments:

- `SSH_PRIVATE_KEY`
- `SSH_KNOWN_HOSTS`
- `SSH_USER`
- `SSH_HOST`
- `VITE_ENDPOINT`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_FIREBASE_MEASUREMENT_ID`
- `VITE_FIREBASE_VAPID_KEY`
- `VITE_SUMMARY_MODEL`
- `VITE_SENTRY_DSN`
- `VITE_GA_MEASUREMENT_ID`

## Server Mounts

The backend Docker Compose file mounts host directory `/secrets/teramina` into the container at `/secrets`.

If JSON secrets are not provided, place service account files here:

- `/secrets/teramina/gcs-sa.json`
- `/secrets/teramina/firebase-sa.json`

Prefer compact JSON GitHub secrets for hosted deployments. Use file mounts only when the server secret management process owns rotation and permissions.

## Expected Server Checkout Paths

The deploy workflow assumes the SSH server has these existing checkouts:

- backend: `~/teramina/core-be-teramina/`
- frontend: `~/teramina/fe-teramina/`

Each checkout must track `origin/main` and contain the relevant `docker-compose.yml`.

## Pre-Deployment Checks

Run these before tagging `production-*`:

```bash
cd fe-teramina-main
npm run lint
npm run typecheck
npm run test
npm run build

cd ../core-be-teramina-main
python manage.py check --deploy
python -m pytest -q
```

For dependency changes, rebuild images from scratch and run the backend suite inside the image before tagging production.

## Secret Rotation

Rotate these before go-live if they were ever stored in a local `.env`:

- MongoDB Atlas user password
- `DJANGO_SECRET_KEY`
- `JWT_SECRET_KEY`
- Firebase service account key
- Google Cloud service account key
- OpenAI, Anthropic, Pinecone, and Teramina API keys
