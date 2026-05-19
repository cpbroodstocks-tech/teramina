# Teramina Graph Memory MVP Todo

## Completed In This Pass

- [x] Stabilize existing agent/chat changes so the app still builds and routes still work.
- [x] Add graph-memory primitives beside the existing simple `AgentMemory` model.
- [x] Wire active `farm_id`, `pond_id`, and `cycle_id` into every assistant chat request.
- [x] Add deterministic memory context injection before the assistant responds.
- [x] Add quick prompts without duplicating send logic.
- [x] Verify backend Python syntax, frontend lint, and frontend production build.

## Next Execution Slice

- [x] Add a create-memory API hook in the frontend.
- [x] Add a verified memory creation form to the Memory page.
- [x] Let farmers save facts, preferences, events, advice outcomes, or notes.
- [x] Scope new memories to current farm/pond/cycle context when available.
- [x] Refresh memory review after create/delete.
- [x] Re-run backend syntax checks, frontend lint, and frontend build.

## Next Execution Slice: Pond Memory Panel

- [x] Inspect pond and cycle detail page composition.
- [x] Create a reusable pond memory/history panel.
- [x] Fetch memories scoped by current farm and pond.
- [x] Show recent facts, events, advice outcomes, and notes near the pond/cycle workflow.
- [x] Add an empty state that points farmers to the Memory page.
- [x] Re-run backend syntax checks, frontend lint, and frontend build.

## Next Execution Slice: Tests And Recommendation Contract

- [x] Inspect current backend and frontend test setup.
- [x] Add focused backend tests for memory creation/search/delete behavior where feasible.
- [x] Add focused frontend tests or type-safe coverage for memory page/query behavior where feasible.
- [x] Strengthen the agent prompt so recommendations follow a stable source/reason/confidence format.
- [x] Confirm lightweight response-format post-processing is not needed yet.
- [x] Re-run targeted tests, lint, build, and backend syntax checks.

## Next Execution Slice: Context And Alert Hardening

- [x] Add mocked backend chat tests for no-context, farm-only, and farm+pond+cycle context.
- [x] Verify chat context updates are persisted on existing sessions.
- [x] Add alert dismissal and resolution tests.
- [x] Verify alert resolution creates an advice memory only when the farmer supplies an action note.
- [x] Confirm the agent prompt blocks speculative memory writes.
- [x] Re-run focused backend tests, frontend tests, lint, build, and syntax checks.

## Next Execution Slice: Graph Memory Visibility

- [x] Add backend tests for graph memory payload entities, relations, and observations.
- [x] Add frontend types and query hook for `/agent/memories/graph`.
- [x] Show a compact graph-memory summary on the Memory page.
- [x] Show recent graph observations beside flat memories.
- [x] Extend frontend tests for graph-memory rendering.
- [x] Re-run focused backend tests, frontend tests, lint, build, and syntax checks.

## Next Execution Slice: Memory Lifecycle Integrity

- [x] Link flat memories to graph observations with a stable source reference.
- [x] Delete associated graph observations when farmers delete a memory.
- [x] Preserve fallback cleanup for older graph observations without source references.
- [x] Extend backend tests for graph cleanup after memory delete.
- [x] Re-run backend tests, frontend tests, lint, build, and syntax checks.

## Next Execution Slice: Production Readiness Before Vector Search

- [x] Add API/controller tests for memory list, create, graph, and delete endpoints.
- [x] Add migration/backfill notes for existing memory and graph documents.
- [x] Smoke-test backend startup checks.
- [x] Smoke-test frontend memory route in a running Vite app.
- [x] Decide whether MVP should be committed before vector retrieval work.
- [x] Re-run backend tests, frontend tests, lint, build, and syntax checks.

## Strategic Remaining Work

### Stage 1: Mongo Memory Backfill Gate

- [x] Add a dry-run/apply management command for existing `agent_memories`.
- [x] Backfill missing `memory_observations` with `source_ref=agent_memory:<id>`.
- [x] Attach `source_ref` to legacy matching observations when safe.
- [x] Clamp flat memory and graph observation confidence values into `0.0..1.0`.
- [x] Report duplicate legacy observations for manual review instead of guessing.
- [x] Add focused backend tests for dry-run and apply behavior.
- [x] Re-run backend memory tests and syntax checks.

### Stage 2: Vector Retrieval MVP

- [x] Choose the short-term vector store path for the current Mongo MVP.
- [x] Add embedding provider abstraction with test doubles.
- [x] Add memory embedding fields or companion collection.
- [x] Index verified memories and graph observations after create/backfill.
- [x] Add semantic memory search endpoint/tool with deterministic fallback.
- [x] Add tests for lexical fallback, embedding upsert, and scoped retrieval.

### Stage 3: Retrieval-Aware Chat

- [x] Inject semantically relevant memory snippets into chat context.
- [x] Preserve source, reason, confidence, and context IDs in recommendations.
- [x] Add regression tests for low-DO and harvest-history questions.
- [x] Smoke-test Memory page, Pond panel, and chat drawer together.

### Stage 4: Production Beta Hardening

- [x] Add observability for memory search latency and hit/miss counts.
- [x] Add backend low-confidence review filter path for memory review.
- [x] Add admin/backoffice UI for low-confidence memories.
- [x] Add documented rollback plan for vector indexing changes.
- [x] Decide whether to merge MVP branch or continue toward beta branch.

Decision: continue on the beta branch until the Mongo MVP vector layer and the separate Postgres/pgvector migration work are cleanly separated.

## Backend MVP

- [x] Add memory entity, relation, and observation models.
- [x] Add safe memory schemas with non-mutable defaults.
- [x] Add service methods for memory CRUD and graph-style retrieval.
- [x] Add agent tools for `search_farm_memory`, `save_farm_memory`, `get_cycle_timeline`, and `log_farmer_action`.
- [x] Ensure agent responses include source, reason, and confidence for recommendations.
- [x] Add task/reminder model and endpoints for follow-up workflows.
- [x] Add alert resolution metadata and task linkage for critical alerts.
- [x] Add tests for memory create/search/delete and memory context handling.

## Frontend MVP

- [x] Restore chat history when the drawer opens.
- [x] Send page context to `/agent/chat`.
- [x] Add quick prompts without duplicating send logic.
- [x] Show alert severities correctly for `critical`, `warning`, and `info`.
- [x] Add a simple memory review screen: list, filter, delete.
- [x] Add per-pond memory/history panel.

## Data And Retrieval

- [x] Keep MongoEngine implementation for MVP to avoid a broad DB migration.
- [x] Add source, confidence, verification, and expiry fields to every memory.
- [x] Add graph relations for farm/pond/cycle memory context.
- [x] Keep flat memory and graph observation lifecycle in sync.
- [ ] Add vector search later after graph-memory CRUD is stable.
- [ ] Replace `text-embedding-ada-002` only when retrieval is being actively upgraded.

## Validation

- [x] Run backend syntax/import checks.
- [x] Run frontend lint/build for changed chat files.
- [x] Test chat with no context, farm-only context, and farm+pond+cycle context.
- [x] Test alert dismissal and resolution separately.
- [x] Confirm no assistant memory is saved for speculative claims.

## Deferred

- [ ] Neo4j/Memgraph migration.
- [ ] Full graph visualization.
- [ ] Autonomous unconfirmed memory writes.
- [ ] Native mobile application.
- [ ] Temporal workflows.
