# Teramina

Combined repository for the Teramina shrimp farming management platform.

## Projects

- `fe-teramina-main/` - React + Vite frontend.
- `core-be-teramina-main/` - Django + Django Ninja backend.

## Frontend

```bash
cd fe-teramina-main
yarn install
yarn dev
yarn lint
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
MONGOATLAS_USER=
MONGOATLAS_PASSWORD=
MONGOATLAS_HOST=
MONGOATLAS_DATABASE=
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=
```

Set either `MONGODB_URI` or the `MONGOATLAS_*` variables. `MONGODB_URI` is preferred for deployments and CI because it supports both `mongodb://` and `mongodb+srv://` connection strings.

Keep `.env` files and service account credentials out of git.

## Quality Gates

Before merging production-bound work:

```bash
cd fe-teramina-main && yarn lint && yarn test && yarn build
cd ../core-be-teramina-main && pytest -q && python manage.py check --deploy
```

The frontend uses Yarn as the lockfile source of truth.
