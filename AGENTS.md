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
- `core-be-teramina-main/` — Django 4 + Django Ninja backend

---

## Frontend (`fe-teramina-main/`)

**Stack:** React 18, Vite 3, MUI 5, Firebase auth, Axios, Formik+Yup, i18next, ECharts, React Router v6

### Commands

```bash
yarn install       # Install dependencies
yarn dev           # Dev server with HMR
yarn build         # Production build (outputs to dist/)
yarn preview       # Preview production build on port 5173
yarn lint          # ESLint check
yarn lint:fix      # Auto-fix lint issues
```

Pre-commit hooks (Husky) automatically run `lint:fix` then `lint` on staged files.

### Lint rules (`.eslintrc.js`)
- Double quotes, 2-space indent, 170-char max line length
- No `console` statements
- `react-hooks/exhaustive-deps` is disabled intentionally — do not add missing deps without understanding the reason

### Architecture

```
src/
├── pages/          # Route-level page components
├── containers/     # Stateful container components (data fetching, logic)
├── components/     # Reusable presentational components
├── hoc/            # Higher-order components — withFilter (per section), withModal
├── hooks/          # Custom hooks (useDebounce, useFirebase, useLocalStorage, etc.)
├── store/          # Context-based state (user, toast, farm-management, wizard)
├── widgets/        # Dashboard widget components
├── routes/         # Route definitions
├── theme/          # MUI theme customization
├── helper/         # Utility functions
├── locales/        # i18n translation files
└── libraries/      # Custom library wrappers
```

**State management** uses React Context API (not Redux). Key contexts: user auth, toast notifications, farm management, wizard (multi-step forms).

**Path aliases** (configured in `vite.config.js` and `jsconfig.json`): `components`, `containers`, `hoc`, `pages`, `routes`, `theme`, `libraries`, `helper`, `widgets`, `hooks`, `store`, `locales` — import directly without relative paths.

**Bundle splitting** in `vite.config.js` manually splits vendor chunks (MUI, Firebase, ECharts, etc.) to optimize loading.

---

## Backend (`core-be-teramina-main/`)

**Stack:** Django 4.0.5, Django Ninja (type-safe REST), MongoEngine (MongoDB ORM), Uvicorn, Pandas/NumPy, LangChain + OpenAI, FAISS/Pinecone

### Commands

```bash
pip install -r requirements.txt

python manage.py runserver                                                    # Dev server
python3 manage.py runserver_plus --cert-file cert.pem --key-file key.pem     # Dev with HTTPS
```

API docs available at `/api/docs` when running locally.

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
| `summarize/` | LangChain + OpenAI AI-generated farm insights |
| `helpers/` | Shared utilities (data preprocessing, DB updater, report service, plots) |
| `data_generator/` | Sample data generation for testing |

**`formulas/harvest_optimization_formula.py`** implements Kalman filter–based state estimation for harvest optimization — the most mathematically complex part of the system.

**Vector search** (`helpers/pinecone_data_indexing.py`, `helpers/data_indexing.py`) indexes farm reports into FAISS/Pinecone for semantic retrieval.

**Settings** (`teramina/settings.py`): MongoDB Atlas, Firebase Admin SDK, and Google Cloud Storage are all configured via environment variables. CORS is open to all origins.
