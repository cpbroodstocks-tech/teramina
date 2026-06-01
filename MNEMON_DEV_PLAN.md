# Teramina Mnemon Development Plan

## Goal

Build Mnemon as Teramina's farmer-facing graph memory layer: the assistant should know the active farm, pond, cycle, and page context, retrieve relevant prior facts/actions/patterns, ask for confirmation before storing inferred memories, and surface remembered context where farmers make decisions.

Mnemon serves the broader product framework in `CYBERNETIC_PRODUCT_FRAMEWORK.md`: it exists to improve the farm control loop by preserving context, surfacing prior responses, explaining uncertainty, and helping farmers close the loop after action.

## Non-Negotiable Principles

- Current MVP stays aligned with the existing Django Ninja + MongoEngine platform.
- Postgres/pgvector work is a future migration track and must not be mixed into the Mongo MVP branch.
- Mnemon recommendations must follow the cybernetic product contract: state, risk, confidence, action, tradeoff, next check, and source.
- This document is the active implementation plan for the current beta branch. See `SECOND_BRAIN_ARCHITECTURE_DECISION.md` for the accepted architecture boundary and deferred tracks.
- Live farm data beats stale memory.
- Memory is not saved silently unless it is direct verified data or a farmer-confirmed action/outcome.
- Every recommendation should cite source, reason, confidence, and relevant context IDs.
- Graph visualization is deferred; graph structure is useful internally before it is visualized.

## Architecture

### Frontend Context Contract

Every assistant chat request must send:

```json
{
  "message": "Why is DO low?",
  "session_id": "session-id",
  "farm_id": "farm-id",
  "pond_id": "pond-id",
  "cycle_id": "cycle-id",
  "page_context": {
    "route": "/dashboard/cycle/123",
    "page_type": "cycle_detail",
    "farm_id": "farm-id",
    "pond_id": "pond-id",
    "cycle_id": "cycle-id",
    "filters": {}
  }
}
```

Context priority:

1. URL params
2. Active page/component props
3. Selected dashboard filters
4. Local storage fallback

### Backend Memory Model

Mongo MVP source of truth:

- `agent_memories`: farmer-visible facts/preferences/events/advice/notes.
- `memory_entities`: graph nodes for farms, ponds, cycles, patterns, actions, issues.
- `memory_relations`: graph edges such as `contains`, `has_pattern`, `responded_to`.
- `memory_observations`: graph-attached text, source, confidence, lifecycle metadata.

### Agent Tools

Required tools:

- `search_memory`: scoped search over farmer memory.
- `get_pond_history`: recurring issues, what worked, prior harvest outcomes, and notes for one pond.
- `save_farm_memory`: persists confirmed memory only.
- `log_farmer_action`: stores confirmed actions and outcomes.
- Existing farm/cycle metric tools remain source of truth for live numbers.

## Implementation Stages

### Stage 1: Context-Aware Chat Foundation

- Add a frontend context resolver.
- Send `farm_id`, `pond_id`, `cycle_id`, and `page_context` to `/agent/chat` and `/agent/chat/stream`.
- Add backend schema support for `page_context`.
- Persist `page_context` on chat sessions.
- Add tests proving URL params override localStorage.
- Add tests proving active pond/cycle pages send correct context.

Success criteria:

- Memory retrieval is scoped by actual page context.
- No farmer needs to type IDs manually.
- Context survives session restore.

### Stage 2: Mnemon Memory Tools

- Add `search_memory` alias/tool with clear scoped semantics.
- Add `get_pond_history` tool.
- Return grouped pond history:
  - recurring issues
  - what worked before
  - past harvest outcomes
  - notes
- Add backend tests for pond history scope and grouping.

### Stage 3: Memory UI

- Add assistant memory chips:
  - `Remembered: prefers harvest size 40`
  - `Remembered: Pond B has recurring low DO after rain`
- Improve Memory review page:
  - facts
  - preferences
  - pond patterns
  - past actions
  - delete/correct controls
- Improve per-pond history panel:
  - recurring issues
  - what worked before
  - harvest outcomes
  - notes

### Stage 4: Confirmation UX

- Detect candidate memories from chat.
- Show: `Should I remember this for future recommendations?`
- Save only after farmer confirmation.
- Allow correction before saving.
- Never save speculative claims automatically.

### Stage 5: Pattern Detection Jobs

Add periodic jobs:

- `detect_recurring_low_do_patterns()`
- `detect_growth_lag_patterns()`
- `detect_high_feed_leftover_patterns()`
- `detect_harvest_outcome_patterns()`
- `detect_cost_overrun_patterns()`

Store graph outputs:

```text
Pond A -> has_pattern -> low_DO_after_DOC_40
Pond A -> responded_to -> increased_aeration
low_DO_after_DOC_40 -> risk_level -> medium
```

### Stage 6: Evaluation Suite

Create farmer question evals:

- "What happened last time DO was low?"
- "What does this farmer usually do before harvest?"
- "Which pond has the most recurring water quality issues?"
- "Should I feed less today?"
- "Why are you recommending harvest next week?"

Evaluate:

- correct entity retrieval
- correct time period
- no invented numbers
- live data over stale memory
- Bahasa Indonesia quality
- recommendation usefulness
- farmer correction handling

## MVP Scope

Build now:

- Store farmer preferences.
- Store pond recurring issues.
- Store actions and outcomes from alerts.
- Retrieve memory during chat.
- Show/delete memories in UI.
- Add full page context.
- Add confirmation before inferred memory writes.

Do not build now:

- Full graph visualization.
- Autonomous unconfirmed memory writes.
- Complex multi-agent planning.
- Neo4j migration.
- Native mobile app.
- Postgres/pgvector migration.

## Current Progress Snapshot

- Memory CRUD: done, including create, verify, correct/update, delete, graph sync, and embedding sync.
- Memory review UI: done for list, filter, create, verify, correct/update, delete, and low-confidence review.
- Per-pond panel: done for the MVP grouped memory surface.
- Alert action outcome memory: done.
- Chat context IDs: done for assistant chat payload.
- `page_context`: done for assistant chat payload, backend schema, session persistence, and stream completion payload.
- `search_memory`: done.
- `get_pond_history`: done.
- Confirmation UX: done for explicit farmer "Remember ..." chat turns, including correction before save.
- Pattern jobs: done for low DO, growth lag, high feed leftover, harvest window, and cost overrun, with daily Celery Beat scheduling through `agent.detect_all_patterns`.
- Eval suite: done as deterministic Mnemon quality gates.
- Silent unconfirmed memory writes: blocked in `save_farm_memory`; the tool now requires explicit confirmation.

## Immediate Next Stage

Production hardening status:

- Focused backend/frontend checks: done.
- Local app boot smoke: done for frontend `/` and backend `/api/docs`.
- Authenticated farmer chat + memory click-through: requires a real Firebase session and seeded farmer data.
- Postgres/pgvector runtime hooks: parked outside the beta branch on `mnemon-experimental-voice-daily-log-pg`.

## Branch Hygiene Decision

The following files are **Postgres/pgvector future-track** and were moved off this branch:

- `core-be-teramina-main/teramina/core_pg/` — future Postgres app (models, sync, migrations).
- `core-be-teramina-main/teramina/agent/models/pg_models.py` — Django ORM counterparts of Mongo models.
- `core-be-teramina-main/teramina/agent/migrations/` — Django ORM migrations generated for the pg models.

These should stay on `mnemon-experimental-voice-daily-log-pg` until the Postgres migration track is formally started. The MongoEngine Mnemon beta branch should remain clean of these files.
