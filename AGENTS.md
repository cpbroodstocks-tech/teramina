# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

---

## Repository Structure

This is a **shrimp farming management platform** (Teramina) with two sub-projects:

- `fe-teramina-main/` — React 18 + Vite frontend
- `core-be-teramina-main/` — Django + Django Ninja backend

---

## Frontend (`fe-teramina-main/`)

**Stack:** React 18, Vite 6, MUI 9, Firebase auth, Axios, TanStack Query, Zustand, React Hook Form + Zod, i18next, ECharts, React Router 7, Vitest/MSW

### Commands

```bash
yarn install       # Install dependencies
yarn dev           # Dev server with HMR
yarn build         # Production build (outputs to dist/)
yarn preview       # Preview production build on port 5173
yarn lint          # ESLint check
yarn lint:fix      # Auto-fix lint issues
yarn typecheck     # TypeScript check
yarn test          # Vitest test suite
```

Pre-commit hooks (Husky) automatically run `lint:fix` then `lint` on staged files.

### Lint rules (`.eslintrc.js`)
- Double quotes, 2-space indent, 170-char max line length
- No `console` statements
- `react-hooks/exhaustive-deps` is disabled intentionally — do not add missing deps without understanding the reason

### Architecture

```
src/
├── features/       # Feature-owned pages, components, query hooks, schemas
├── pages/          # Route-level shims and small shell pages
├── components/     # Reusable presentational components
├── hooks/          # Custom hooks (useDebounce, useFirebase, useLocalStorage, etc.)
├── lib/            # Shared runtime libraries such as query client
├── store/          # Zustand stores
├── routes/         # Route definitions
├── theme/          # MUI theme customization
├── helper/         # Utility functions
├── locales/        # i18n translation files
├── libraries/      # Custom library wrappers
└── tests/          # Vitest, React Testing Library, MSW tests
```

**State management** uses TanStack Query for server state and Zustand for client state. Avoid reintroducing Context stores for data fetching or global UI state.

**Path aliases** are configured in `vite.config.js` and `tsconfig.json`: `components`, `features`, `helper`, `hooks`, `lib`, `libraries`, `locales`, `pages`, `routes`, `store`, `theme`, and `widgets` (mapped to `features/dashboard`). Import through aliases when that matches existing local style.

**Bundle splitting** in `vite.config.js` manually splits vendor chunks (MUI, Firebase, ECharts, etc.) to optimize loading.

New frontend files should be TypeScript where practical. Existing `.js`/`.jsx` files do not need broad conversion unless the task already touches them.

---

## Backend (`core-be-teramina-main/`)

**Stack:** Django 5.2, Django Ninja, Pydantic 2, MongoEngine/MongoDB, Celery + Redis, Pandas/NumPy, Google Sheets API, Firebase Admin SDK, Anthropic/OpenAI, Pinecone-compatible retrieval helpers, Sentry

### Commands

```bash
pip install -r requirements.txt

python manage.py runserver                 # Dev server
python manage.py check                     # Django checks
python manage.py check --deploy            # Production deployment checks
python -m pytest -q                        # Backend test suite
python3 manage.py runserver_plus --cert-file cert.pem --key-file key.pem  # Dev with HTTPS, when django-extensions supports it locally
```

API docs are available at `/api/docs` when running locally. Health checks are available at `/health/`.

### Architecture

All modules follow the same layered pattern:

```
<module>/
├── models.py       # MongoEngine document models
├── schemas.py      # Pydantic request/response schemas (Django Ninja)
├── services.py     # Business logic
├── controllers.py  # Django Ninja route handlers
└── api.py          # Router registration
```

Key modules:

| Module | Responsibility |
|--------|---------------|
| `authentication/` | JWT-based auth via Firebase Admin SDK |
| `farm/`, `pond/`, `cycle/` | Core domain entities |
| `cycle_data/` | Time-series water & farm data per pond |
| `harvest/`, `feeding/` | Harvest and feeding operations |
| `formulas/` | Mathematical models: biomass, weight, SGR, population, cost, revenue |
| `dashboard/`, `water_quality_dashboard/` | Aggregated metric views |
| `benchmark/` | Cohort benchmarking and scheduled recomputation |
| `google_sheets/` | Sheet template creation, preview, sync, logs, and feedback |
| `agent/` | Mnemon assistant, memory, alerts, tasks, timeline, and evals |
| `pl_report/` | Cycle/farm/year profit-and-loss reports and share links |
| `summarize/` | LangChain + OpenAI AI-generated farm insights |
| `helpers/` | Shared utilities (data preprocessing, DB updater, report service, plots) |
| `data_generator/` | Sample data generation for testing |

**`formulas/harvest_optimization_formula.py`** implements Kalman filter–based state estimation for harvest optimization — the most mathematically complex part of the system.

**Second Brain / Mnemon** currently stays on MongoEngine + MongoDB. Postgres, TimescaleDB, pgvector, voice notes, offline daily log, Temporal workflows, native mobile, and full graph visualization are deferred until the beta gate in `SECOND_BRAIN_ARCHITECTURE_DECISION.md` is met.

**Settings** (`teramina/settings.py`): MongoDB, Firebase Admin SDK, Google Cloud Storage, Redis/Celery, CORS/CSRF, Sentry, and production security settings are configured via environment variables. Do not relax production env validation without a deployment reason.
