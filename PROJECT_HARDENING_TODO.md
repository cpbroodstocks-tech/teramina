# Teramina Production Hardening Todo

## Goal

Move Teramina from a strong beta to a production-ready service without adding new product scope.

## P0: Correctness and Security

- [x] Fix the authenticated pond active-cycle endpoint and add controller coverage.
- [x] Replace import-time MongoEngine datetime defaults with callable defaults.
- [x] Make rate-limit counters atomic and isolate buckets by route limit.
- [x] Prevent repeated Axios refresh attempts after a retried request returns 401.
- [x] Audit ownership and role enforcement across all API routes, with negative tests for cross-user access.
- [x] Protect dashboard farm/cycle reads and report creation with ownership checks.
- [x] Protect water-quality reads and exports with cycle ownership checks.
- [x] Restrict global water-quality variable mutation to admins.
- [x] Treat malformed resource IDs as unauthorized instead of raising server errors.
- [x] Bind asynchronous report task IDs to the requesting user before allowing result polling.
- [x] Bind external summary task IDs to the requesting user before allowing result polling.
- [x] Verify credential files and secret values are absent from Git history.
- [ ] Rotate locally present API and service-account credentials in their provider consoles, then replace the ignored local values.

## P1: Reproducible Verification

- [x] Synchronize the backend virtualenv from `requirements.txt` and run the complete backend suite.
- [x] Run `python manage.py check --deploy` in a clean CI-equivalent environment.
- [x] Run frontend typecheck, lint, tests, and production build.
- [x] Add backend and frontend coverage reporting with measured non-regression thresholds.
- [x] Remove React/MUI warnings from the frontend test output.

## P1: Staging and Operations

- [ ] Run the authenticated staging smoke checklist with a real Firebase session and seeded farmer data.
- [ ] Exercise MongoDB, Redis, Celery worker/beat, Google Sheets, storage, report generation, and Mnemon end to end.
- [ ] Test backup creation and perform a documented restore drill.
- [ ] Verify alerting for API errors, worker failures, queue backlog, database connectivity, and failed scheduled jobs.
- [ ] Test deployment rollback and secret rotation procedures in staging.
- [x] Define service-level objectives for availability, latency, background-job completion, and recovery.

## P2: Maintainability and Performance

- [ ] Split the commercial admin page by workflow after capturing behavior with focused tests.
- [x] Extract shared commercial-admin section/navigation and the beta-access workflow without changing behavior.
- [x] Review other 500+ line frontend components and document stable extraction boundaries.
- [x] Add CI bundle budgets; constrained mobile testing still requires a browser/network profile.
- [x] Reduce the PWA precache and runtime-cache JavaScript and images on demand.
- [x] Remove duplicate nested CI workflows after confirming the root workflows are authoritative.
- [x] Document and locally verify the clean setup and quality-gate path.

## Product Gate

- [ ] Freeze new major subsystems until the hardening and staging gates pass.
- [ ] Complete real-user farm pilots covering setup, daily operation, reporting, and recovery from bad data.
- [ ] Validate the full commercial journey from lead through manual payment and delivery.
- [ ] Remove or defer surfaces that pilots do not use before expanding the product scope.

## Production Exit Criteria

- [ ] All automated checks pass from clean environments.
- [ ] No known P0 correctness or authorization defects remain.
- [ ] Authenticated staging smoke tests and restore drills pass.
- [ ] Monitoring, rollback, and incident ownership are documented and exercised.
- [ ] Pilot users complete the core farm workflow without engineering intervention.
