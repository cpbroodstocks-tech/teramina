# Frontend Modernization Plan — Teramina

**Project:** `fe-teramina-main/`
**Date:** 2026-04-17
**Approach:** Incremental — each phase is independently shippable. Never a big-bang rewrite.

## Product Context

Frontend modernization should support the product direction in `CYBERNETIC_PRODUCT_FRAMEWORK.md`. The UI should increasingly present pond state, trajectory, control margin, uncertainty, and follow-up actions, not just isolated dashboard metrics. Refactors should preserve that direction and avoid generic redesign work that does not improve the farmer control loop.

---

## Historical State Snapshot

This snapshot reflects the frontend state when this modernization plan was first written. Some items have already moved forward; verify against `package.json`, `vite.config.js`, and the current test tree before treating a row as still open.

| Area | Current | Problem |
|------|---------|---------|
| Build | Vite 3.2.3 | Two major versions behind (v6 current) |
| Language | JavaScript (.js/.jsx) | No type safety on a data-heavy domain |
| State (server) | Custom Context + Axios | Manual loading/error/cache management per feature |
| State (client) | React Context + useReducer | Re-renders all consumers on any change |
| Forms | Formik 2.1.4 + Yup 0.28 | Controlled re-renders on every keystroke; Yup types don't infer well |
| Component Pattern | HOCs (`withModal`, `withFilter`, `withFarmManagementContext`) | Verbose, harder to type, superseded by hooks |
| Folder Structure | Type-based (`containers/`, `pages/`, `components/`) | Feature code scattered across 3+ directories |
| Testing | None | No safety net for migration or future changes |
| MUI | 5.14.8 | One major version behind; `@mui/styles` (legacy) still in use |

## Closure Status — 2026-05-21

The frontend is now in closure mode for this plan rather than initial migration mode.

| Area | Status | Notes |
|------|--------|-------|
| Build | Complete | Vite 6 build path is active. Production build should remain part of closure verification. |
| TypeScript | Partial | `tsconfig.json` exists and relaxed typecheck passes, but much of the app remains `.js/.jsx`. `src/types/api.ts` is not committed because generation currently depends on a live backend OpenAPI endpoint. |
| Server state | Mostly complete | Direct Axios usage has been moved behind query/API modules. Remaining fetch work should preserve this boundary. |
| Client state | Mostly complete | `src/store/` contains Zustand stores only. |
| Forms | Mostly complete | Formik/Yup are removed; RHF/Zod are active. Some local variable names may still say `formik*` and should be cleaned when touched. |
| Feature structure | Mostly complete | Large route implementations have moved under `features/*`; `src/pages/` is now route shims plus small shell pages. |
| HOCs | Complete | `src/hoc/` is gone and stale aliases have been removed. |
| Tests | Complete | Vitest/RTL/MSW infrastructure exists; `npm run test` passed on 2026-05-21 with 28 files and 165 tests. |
| Dependencies | Mostly complete | Legacy packages called out by the original plan are removed or no longer referenced in config. |

### OpenAPI Type Generation

`npm run gen:types` currently runs `npx openapi-typescript http://localhost:8000/api/docs/openapi.json -o src/types/api.ts`.
On 2026-05-21 this failed because `localhost:8000` refused the schema request. Treat generated API types as a backend-available task:

1. Start the Django backend with API docs available at `/api/docs/openapi.json`.
2. Run `npm run gen:types`.
3. Commit `src/types/api.ts` only when the generated output is real and repeatable.

---

## Phase 1 — Build Upgrade

**Goal:** Vite 3 → Vite 6, update adjacent tooling.
**Risk:** Low. Isolated to config and dev tooling.
**Touches:** `package.json`, `vite.config.js`, `.eslintrc.js`

### Steps

1. Upgrade Vite and React plugin:
   ```
   vite: 3.2.3 → 6.x
   @vitejs/plugin-react: 2.2.0 → 4.x
   vite-plugin-pwa: 0.14.1 → latest
   ```
2. Audit breaking changes in Vite 4, 5, 6 changelogs — mainly plugin API and env variable handling.
3. Verify `vite.config.js` manual chunk splitting still works (likely needs `build.rollupOptions` syntax check).
4. Update `@babel/eslint-parser` and eslint plugins to compatible versions.
5. Smoke test: `yarn dev`, `yarn build`, `yarn preview`.

### Success Criteria
- Dev server starts, HMR works
- Production build output is identical in structure
- No new console errors

---

## Phase 2 — TypeScript

**Goal:** Add TypeScript incrementally. All new files written in `.tsx`. Existing files migrate on touch.
**Risk:** Medium. Requires tsconfig setup and alias wiring. No runtime changes.

### Steps

1. Add TypeScript:
   ```
   typescript
   @types/react
   @types/react-dom
   @types/node
   ```
2. Replace `jsconfig.json` with `tsconfig.json` — carry over `baseUrl` and path aliases.
3. Update `vite.config.js` to reference `.ts`/`.tsx` extensions.
4. Switch ESLint parser from `@babel/eslint-parser` to `@typescript-eslint/parser` + plugin.
5. Generate TypeScript types from the backend OpenAPI spec:
   ```
   npx openapi-typescript http://localhost:8000/api/docs/openapi.json -o src/types/api.ts
   ```
   Wire this as a `yarn gen:types` script.
6. Set `"strict": false` initially — tighten over time.
7. Write all new files as `.tsx`. Migrate existing files to `.tsx` only when you touch them.

### Migration Rule
- New file → always `.tsx`
- Editing existing `.jsx` file → rename to `.tsx` in the same PR
- Never batch-rename files without accompanying logic changes

### Success Criteria
- TypeScript compiles with zero errors (some `any` is acceptable initially)
- API response types generated from backend schema are importable
- ESLint still passes

---

## Phase 3 — Server State (TanStack Query)

**Goal:** Replace `FarmManagementContext` + `withFarmManagementContext` HOC + raw Axios calls with TanStack Query hooks.
**Risk:** Medium. This is the most impactful structural change. Do one module at a time.

### What Gets Replaced
- `src/store/farm-management/index.jsx` — the generic fetch context
- `src/hoc/withFarmManagementContext/index.jsx` — HOC provider wrapper
- All direct `axios.get()` calls inside containers and pages

### Steps

1. Install: `@tanstack/react-query`
2. Add `QueryClientProvider` to `src/index.jsx` wrapping the app.
3. Add React Query Devtools in development.
4. Create `src/lib/queryClient.ts` — configure stale time, retry behavior.
5. Migrate modules one at a time, starting with the simplest (read-only lists):

   **Order:**
   - `farm` list/detail
   - `pond` list/detail
   - `cycle` list/detail
   - `cycle_data` (time-series — most complex, do last)
   - `harvest`, `feeding`
   - `dashboard` / `water_quality_dashboard`

6. Per module, create `src/features/<module>/queries.ts`:
   ```ts
   // Example
   export const useFarmList = () =>
     useQuery({ queryKey: ["farms"], queryFn: () => api.get("/farm/list-farm") });
   ```
7. Replace `withFarmManagementContext` usage with direct `useQuery` hook in the container.
8. Remove `src/store/farm-management/` and `src/hoc/withFarmManagementContext/` once all consumers are migrated.

### Success Criteria
- No remaining `withFarmManagementContext` usage
- `FarmManagementContext` store deleted
- All data fetching uses `useQuery` / `useMutation`
- Manual loading/error state code removed from containers

---

## Phase 4 — Client State (Zustand)

**Goal:** Replace React Context stores for non-server state with Zustand.
**Risk:** Low–medium. Touches global state wiring.

### What Gets Replaced

| Current Store | Type | Replace With |
|---|---|---|
| `store/user/` | User identity | Zustand store |
| `store/toast/` | Notifications | Zustand store |
| `store/wizard/` | Multi-step form state | Zustand store (or local state if only one wizard) |

`store/farm-management/` is already removed in Phase 3.

### Steps

1. Install: `zustand`
2. Create `src/store/user.store.ts`, `src/store/toast.store.ts`, etc.
3. Migrate consumers one store at a time.
4. Remove old Context providers from `src/index.jsx` as each store is migrated.
5. Keep the `useUserContext`, `useToastContext` hook names as thin wrappers around Zustand — avoids touching every call site.

### Success Criteria
- No remaining `UserContextProvider`, `ToastContextProvider` in JSX tree
- All stores are Zustand-based
- `src/store/` contains only `.ts` store files, no `.jsx` providers

---

## Phase 5 — Forms (React Hook Form + Zod)

**Goal:** Replace Formik + Yup with React Hook Form + Zod.
**Risk:** Low per form. Can be done one form at a time with no shared dependencies.

### Forms in the Codebase
- `containers/farm/new-farm/` — complex (cascading dropdowns, file upload, 334 lines)
- `containers/farm/modal-edit-farm/`
- `pages/dashboard/profile_edit/` — file upload with FormData
- Feeding, cycle, pond forms (across containers)

### Steps (per form)

1. Replace `useFormik({...})` with `useForm<FormSchema>()`.
2. Replace `Yup.object().shape({...})` with `z.object({...})` — use `zodResolver`.
3. Infer the TypeScript type from the schema: `type FormValues = z.infer<typeof schema>`.
4. Replace `formik.handleChange` / `formik.values.x` with `register("x")` + `Controller` for MUI inputs.
5. For file upload: use `Controller` with `setValue` — same pattern as current `formik.setFieldValue`.
6. For cascading dropdowns: use `watch("provinsi")` to trigger dependent field resets via `resetField`.

### Key Differences to Handle
- MUI `TextField` needs `Controller` wrapper (uncontrolled → controlled at RHF boundary)
- `formik.isSubmitting` → `formState.isSubmitting`
- `formik.touched.field` → `formState.errors.field` (RHF combines touched+error)
- `enableReinitialize` → use `reset(newValues)` in a `useEffect` on data load

### Success Criteria
- No remaining `formik` or `yup` imports
- `formik` and `yup` removed from `package.json`
- All forms pass same validation as before

---

## Phase 6 — Folder Restructure (Feature-Based)

**Goal:** Move from type-based to feature-based layout. Colocate all code for a feature.
**Risk:** Low if done with path aliases. No logic changes — pure file moves.

### Target Structure

```
src/
├── features/
│   ├── farm/
│   │   ├── FarmList.tsx
│   │   ├── FarmForm.tsx
│   │   ├── farm.queries.ts       ← TanStack Query hooks (from Phase 3)
│   │   ├── farm.schema.ts        ← Zod schema (from Phase 5)
│   │   └── farm.types.ts
│   ├── pond/
│   ├── cycle/
│   ├── harvest/
│   ├── feeding/
│   └── dashboard/
├── components/                   ← Truly shared UI only (Loader, Error, Toast, etc.)
├── hooks/                        ← Truly shared hooks only
├── store/                        ← Zustand stores (from Phase 4)
├── lib/                          ← queryClient, axios instance, firebase
├── types/                        ← Generated API types, shared domain types
├── routes/
├── theme/
└── locales/
```

### Steps
1. Create `src/features/` directory.
2. Move one feature at a time, starting with the smallest (`harvest`).
3. Update path aliases in `vite.config.js` and `tsconfig.json` after each move.
4. Verify no broken imports after each feature move.

### Success Criteria
- `src/containers/` directory deleted
- `src/pages/` contains only thin route-entry components (< 30 lines each)
- Each feature directory is self-contained

---

## Phase 7 — HOC Elimination

**Goal:** Replace remaining HOCs with hooks and composition.
**Risk:** Low. `withFarmManagementContext` already removed in Phase 3.

### Remaining HOCs After Phase 3

| HOC | Replacement |
|---|---|
| `withModal` | `useModal` hook returning `{ open, onOpen, onClose }` + `Dialog` inline |
| `withFilter` variants | `useFilter` hook with local state |

### Steps
1. Create `src/hooks/useModal.ts`.
2. Find all `withModal(...)` call sites.
3. Inline the `Button + Dialog` pattern directly in the container — it's 10–15 lines each.
4. Repeat for `withFilter`.
5. Delete `src/hoc/` directory.

### Success Criteria
- `src/hoc/` directory deleted
- No remaining HOC wrapper patterns

---

## Phase 8 — Testing Infrastructure

**Goal:** Add baseline test coverage as a safety net for the migration and future changes.
**Risk:** Zero — purely additive.

### Stack
- **Vitest** — native Vite test runner, no config overhead
- **React Testing Library** — component testing
- **MSW (Mock Service Worker)** — API mocking at the network level

### Steps
1. Install: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `msw`
2. Add `test` script to `package.json`: `vitest run`
3. Add `test:watch` script: `vitest`
4. Configure `vitest.config.ts` (extend from `vite.config.ts`)
5. Write tests for:
   - All Zod schemas (pure functions, easiest to start)
   - Critical formula-adjacent helpers
   - One query hook per feature (MSW handler)
   - One form per feature (RHF submit behavior)

### Target Coverage (Pragmatic)
- Schemas: 100%
- Query hooks: 1 test each (happy path)
- Forms: 1 test each (submit, validation error)
- Business logic helpers: 80%+

---

## Phase 9 — Dependency Cleanup

**Goal:** Remove dead packages, upgrade stragglers.
**Do this last** — earlier phases will have already removed the hard dependencies.

### Packages to Remove
| Package | Removed When |
|---|---|
| `formik` | Phase 5 complete |
| `yup` | Phase 5 complete |
| `@mui/styles` (legacy MUI v4 compat) | Phase 6+ (replace `makeStyles` with `sx` prop or `styled`) |
| `react-chartjs-2` | Audit — ECharts likely covers all charts |

### Packages to Upgrade
| Package | Current | Target |
|---|---|---|
| `@mui/material` | 5.14.8 | 6.x |
| `@mui/x-data-grid` | 5.17.14 | 7.x |
| `@mui/x-date-pickers` | 5.0.9 | 7.x |
| `react-router-dom` | 6.4.3 | 7.x |
| `firebase` | 9.14.0 | 11.x |
| `axios` | 1.2.0 | 1.x latest |

---

## Principles Throughout

1. **One thing at a time.** Never mix phases in a single PR.
2. **Tests before delete.** Before removing a Context store or HOC, have the replacement working first.
3. **Alias stability.** Don't break import paths — update aliases in lock-step with file moves.
4. **No logic changes during restructure.** Phase 6 (folder move) contains zero logic changes.
5. **Type the boundary first.** When migrating a module, type the API response first, then work inward.

---

## Timeline Estimate (Solo Developer, Part-Time)

| Phase | Effort |
|---|---|
| 1 — Vite upgrade | 0.5 day |
| 2 — TypeScript setup | 1 day |
| 3 — TanStack Query | 3–5 days |
| 4 — Zustand | 1–2 days |
| 5 — React Hook Form | 2–3 days |
| 6 — Folder restructure | 1–2 days |
| 7 — HOC elimination | 1 day |
| 8 — Testing | 2–3 days |
| 9 — Cleanup | 0.5 day |
| **Total** | **~12–18 days** |
