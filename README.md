# Teramina

Combined repository for the Teramina shrimp farming management platform.

## Projects

- `fe-teramina-main/` - React + Vite frontend.
- `core-be-teramina-main/` - Django + Django Ninja backend.

## Current Documentation

- `AGENTS.md` - engineering guidance and current architecture notes.
- `CYBERNETIC_PRODUCT_FRAMEWORK.md` - product direction and recommendation contract.
- `TERAMINA_COMMERCIAL_LAYER_DEV_PLAN.md` - plan for paid content, advisory workflows, manual access, and commercial reports.
- `COMMERCIAL_LAYER_MANUAL_QA.md` - seed, manual access, advisory intake, and report-delivery QA checklist.
- `MNEMON_DEV_PLAN.md` - active MongoEngine Mnemon implementation plan.
- `MNEMON_BETA_TODO.md` - current beta readiness checklist.
- `MNEMON_BETA_RUNBOOK.md` - beta smoke test, backfill, Celery, and rollout procedure.
- `SECOND_BRAIN_ARCHITECTURE_DECISION.md` - accepted decision to keep the current beta on MongoEngine/MongoDB.
- `GOOGLE_SHEETS_INTEGRATION_TODO.md` - remaining Google Sheets hardening work.
- `GOOGLE_SHEETS_MANUAL_QA.md` - manual QA checklist for real Google Sheets sync.
- `DEPLOYMENT.md` - production deployment checklist and required secrets.

## Frontend

```bash
cd fe-teramina-main
yarn install
yarn dev
yarn lint
yarn typecheck
yarn test
yarn build
```

Required production environment:

```bash
VITE_ENDPOINT=https://your-api-host/api
```

Do not set `VITE_DEV_TOKEN` outside local development.

## Backend

```bash
cd core-be-teramina-main
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
pytest -q
python manage.py check --deploy
```

Required production environment includes:

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=
JWT_SECRET_KEY=
MONGODB_URI=
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=
```

Set either `MONGODB_URI` or the `MONGOATLAS_*` variables. `MONGODB_URI` is preferred for deployments and CI because it supports both `mongodb://` and `mongodb+srv://` connection strings.

Keep `.env` files and service account credentials out of git.

## Quality Gates

Before merging production-bound work:

```bash
cd fe-teramina-main && yarn lint && yarn typecheck && yarn test && yarn build
cd ../core-be-teramina-main && pytest -q && python manage.py check --deploy
```

The frontend uses Yarn as the lockfile source of truth.
