# Local Development

## Prerequisites

- Node version from `fe-teramina-main/.nvmrc` and Corepack/Yarn 1.22.
- Python 3.11.
- MongoDB and Redis, either local or explicitly configured remote development instances.
- Firebase, Google Cloud, and external AI credentials only for the integrations being exercised.

## Frontend

```bash
cd fe-teramina-main
corepack enable
corepack prepare yarn@1.22.22 --activate
HUSKY=0 yarn install --frozen-lockfile
yarn dev
```

Required local environment:

```bash
VITE_ENDPOINT=http://127.0.0.1:8000/api
```

Verification:

```bash
yarn lint
yarn typecheck
yarn test
yarn test:coverage
yarn build
yarn bundle:check
```

## Backend

```bash
cd core-be-teramina-main
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python manage.py runserver
```

Copy `.env.example` to `.env` and provide development values. At minimum configure Django/JWT secrets, allowed hosts, MongoDB, CORS/CSRF origins, and Redis. Do not use production credentials in local `.env` files.

Verification:

```bash
python -m pytest -q --cov=teramina --cov-report=term-missing --cov-fail-under=57
python manage.py check
```

For deployment checks, use `DJANGO_DEBUG=False`, explicit allowed hosts/origins, and the production-style environment contract before running:

```bash
python manage.py check --deploy
```

## Local Services

The repository Docker Compose files can run service-specific containers, but they do not replace explicit environment setup. Confirm the selected MongoDB database before running seed, backfill, reset, or restore commands.

## Troubleshooting

- If Yarn invokes Husky outside a Git-root-aware directory, install with `HUSKY=0`.
- If Matplotlib cannot write its cache, set `MPLCONFIGDIR` to a writable temporary directory.
- If MongoDB uses an SRV URI, local DNS/network access must allow SRV resolution.
- Generated `dist/`, `coverage/`, `.coverage`, and `coverage.json` files are not source artifacts and should remain untracked.
