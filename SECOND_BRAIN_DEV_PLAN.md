# Teramina Second Brain — Development Plan

## Current Status

This document is the strategic target architecture for Teramina Second Brain. It is **not** the active execution plan for the current beta branch.

The product philosophy and feature-level decision contract are defined in `CYBERNETIC_PRODUCT_FRAMEWORK.md`. This plan should be read as the long-term architecture needed to support that product framework.

The current beta branch intentionally follows the MongoEngine Mnemon track:

- Product framework: `CYBERNETIC_PRODUCT_FRAMEWORK.md`
- Active implementation plan: `MNEMON_DEV_PLAN.md`
- Beta checklist: `MNEMON_BETA_TODO.md`
- Beta rollout procedure: `MNEMON_BETA_RUNBOOK.md`
- Architecture decision: `SECOND_BRAIN_ARCHITECTURE_DECISION.md`
- MongoDB memory backfill notes: `SECOND_BRAIN_MIGRATION_NOTES.md`

Current branch status:

- The MongoEngine-based Mnemon beta is near complete.
- Chat context, scoped memory retrieval, memory CRUD, graph observations, pattern jobs, alerts, tasks, Today view, Memory page, and pond timeline are implemented.
- Authenticated smoke testing with real Firebase session and seeded farmer data remains the main beta gate.
- Postgres, TimescaleDB, pgvector, voice notes, offline daily log, Temporal workflows, and full graph visualization are deferred.

Do not start the deferred migration tracks from this document until the migration gate in `SECOND_BRAIN_ARCHITECTURE_DECISION.md` is met.

**Goal:** Transform Teramina from a data dashboard into a farmer operating system that proactively watches, remembers, and advises.

**Target questions the system must answer:**
- "What should I do today?"
- "Why did growth slow down?"
- "Should I reduce feed?"
- "Is harvest close?"
- "What happened in this pond last cycle?"
- "Remind me if DO stays low tomorrow."
- "Explain this in Bahasa Indonesia for my farm team."

---

## Target Stack

The target stack below is the long-term architecture. The current beta branch remains on Django Ninja + MongoEngine + MongoDB until the documented migration gate is met.

| Layer | Technology |
|-------|-----------|
| Frontend | React 19.2, Vite 8, TypeScript strict, MUI, TanStack Query latest, React Router v7 |
| Backend | Python 3.14.x, Django 6.0.x, Django Ninja + Pydantic schemas |
| Primary DB | PostgreSQL 18.x — relational data, permissions, audit logs, tasks, memory |
| Time-series | TimescaleDB on Postgres — pond sensor readings, cycle measurements |
| Vector/RAG | pgvector (default); Pinecone only if scale or search quality demands it |
| AI layer | OpenAI Agents SDK, GPT-5.4 / GPT-5.4 mini, text-embedding-3-large |
| Background jobs | Celery + Redis (short-term); Temporal for long-running workflows and reminders |
| Realtime | SSE for chat streaming; WebSocket only where two-way realtime is required |
| Mobile/offline | PWA first; React Native/Expo if field usage justifies native |
| Infra | Docker, GitHub Actions, GCP Cloud Run → Kubernetes, Cloud SQL, GCS, Secret Manager, OpenTelemetry, Sentry |

---

## Phase 0 — Technical Audit
**Duration:** 1 week

### Deliverables
- Inventory of all current API routes, models, dashboards, AI features, Pinecone indexing, alert jobs, and frontend state
- Django/Python/package upgrade blocker list
- Decision: MongoDB stays short-term or gradual migration starts
- Baseline metrics: API latency, build health, test coverage, data quality gaps

### Historical Critical Items From The Original Audit

These were the original pre-Phase-1 audit blockers. Several have since been resolved in the MongoEngine Mnemon beta path; verify current status against `MNEMON_DEV_PLAN.md`, `MNEMON_BETA_TODO.md`, and the code before treating any row as open.

| Item | Location | Issue |
|------|----------|-------|
| Agent context gap | `fe-teramina-main/src/components/agent-chat/queries.ts:18` | `useSendAgentMessage` sends only `message` + `session_id` — no `farm_id`, `cycle_id` |
| Cost tool bug | `core-be-teramina-main/teramina/agent/services/agent_tools.py:151` | `CostData.objects(farm_id=cycle_id)` — passes `cycle_id` into `farm_id` filter, silently returns wrong data |
| Token limit | `core-be-teramina-main/teramina/agent/services/agent_service.py:111` | `max_tokens=1024` too low for multi-tool chain; raise to 4096 |
| Chat history on mount | `fe-teramina-main/src/components/agent-chat/index.jsx:37` | Local `messages` state lost on page reload; no session restore from server |
| Pinecone namespace mismatch | `core-be-teramina-main/teramina/helpers/pinecone_data_indexing.py` | Vectors indexed under `user_id`; retrieval defaults to `"default"` namespace — silently misses farm data |

### Success criteria
- Existing app still runs after audit
- All upgrade risks are documented
- No second-brain feature work starts until data ownership and context wiring are understood

---

## Phase 1 — Foundation Modernization
**Duration:** 2–3 weeks

### Frontend
- Upgrade React → 19.2, Vite → 8, enable TypeScript strict mode in controlled steps
- Convert agent chat and core dashboard queries to typed request/response contracts
- **Fix context bug:** `AgentChat` component reads `farmId`/`cycleId` from `farm-management` store (already in `src/store/`) and passes them to every `/agent/chat` POST
- Add session restore: load existing history from `GET /agent/session` on drawer open
- Add quick-prompt chips: "Why is DO low?", "Should I harvest soon?", "What changed this week?"

### Backend
- Upgrade Python → 3.14.x, Django → 6.0.x on a branch; run full smoke tests
- Add `pydantic-settings` for structured environment/settings management
- Standardize all API response envelopes (code, message, payload)
- Add OpenTelemetry tracing (request → service → DB) and Sentry error reporting
- Fix `get_cost_breakdown` — correct the `farm_id=cycle_id` query field bug
- Raise agent `max_tokens` to 4096

### Success criteria
- Build, lint, and all core flows pass
- Agent chat correctly receives and uses `farm_id`/`cycle_id` from whatever page is open
- No farmer needs to type IDs manually

---

## Phase 2 — Data Backbone
**Duration:** 3–5 weeks

### Postgres schema (canonical tables)

```
farms                   — farm profile, location, ownership
ponds                   — pond metadata, size, aerator config
cycles                  — stocking event → harvest event
cycle_observations      — daily roll-up per pond/cycle
water_quality_readings  — raw sensor readings (TimescaleDB hypertable)
feed_events             — feed type, quantity, time, pond
harvest_events          — partial/full harvests, weight, size, price
cost_events             — cost line items per cycle
farmer_notes            — free-form text, photo, voice transcript reference
agent_memories          — durable structured memory (see Phase 3)
recommendations         — agent advice: input, reasoning, source rows, confidence
alerts                  — generated alerts with resolution tracking
workflow_tasks          — follow-up tasks, reminders, assigned to farmer
audit_events            — every write action: who, what, when, old value, new value
```

### Data contracts
Every measurement must carry: `unit`, `source`, `timestamp`, `pond_id`, `cycle_id`, `confidence`.
Every derived metric records `formula_version`.
Every AI answer must be able to cite source rows or aggregates.

### Migration strategy
- Keep MongoDB as read-only legacy source during migration
- Dual-write new data to Postgres from day one of Phase 2
- Backfill historical data batch-by-batch with validation
- Switch reads to Postgres per module once backfill is verified

### Success criteria
- A single cycle timeline can be reconstructed entirely from Postgres
- AI answers can cite the row(s) they used
- TimescaleDB hypertable in place for water quality readings

---

## Phase 3 — Second-Brain Memory
**Duration:** 3–4 weeks

### Memory types

| Type | Examples |
|------|---------|
| Facts | Farm location, pond size, stocking density, aerator setup, water source |
| Preferences | Language, risk tolerance, preferred harvest size, budget ceiling, feed brand |
| Events | Disease incident, low DO event, feed change, partial harvest, power outage |
| Advice history | Recommendation given → farmer action → observed outcome (closed loop) |
| Notes | Manual observations, photos, voice transcripts |

### Memory rules
- Do not store everything blindly — extract only when useful
- Confirm sensitive long-term facts before persisting
- Add `expires_at` for operational assumptions that go stale (e.g., "current stocking density")
- Tag every memory: `verified_data` | `farmer_note` | `ai_inference`
- Memory injected into agent system prompt at query time, filtered by relevance and recency

### `agent_memories` schema (key fields)
```
farm_id, pond_id, cycle_id (nullable)
memory_type: fact | preference | event | advice | note
content: text
tags: string[]
source: user_input | agent_inference | system_observation
confidence: float
created_at, updated_at, expires_at
is_verified: bool
```

### Success criteria
- Farmer can ask "what happened last time this pond had low DO?" and receive a contextual answer with cited events
- Memory entries survive across sessions and chat clears

---

## Phase 4 — Agent Architecture
**Duration:** 4–6 weeks

### Agent pattern: small specialist agents

```
Farm Copilot (orchestrator)
├── Data Analyst          — retrieves metrics, trends, reports
├── Aquaculture Advisor   — interprets water quality, growth, feeding, harvest
├── Workflow Agent        — creates reminders, follow-ups, tasks
└── Safety/Policy Guard   — blocks unsupported medical/chemical certainty,
                            escalates to human expert where needed
```

### Core tool set

| Tool | Purpose |
|------|---------|
| `get_cycle_timeline` | Full event + reading history for a cycle |
| `get_latest_water_quality` | Most recent water quality readings |
| `get_growth_trend` | ABW/SGR trend over N days |
| `get_feeding_summary` | FCR, feed given, leftovers, adjustments |
| `get_harvest_forecast` | Optimal harvest DOC, projected biomass, profit |
| `get_cost_breakdown` | Cost by category for a cycle |
| `search_farm_memory` | Semantic search over `agent_memories` via pgvector |
| `create_reminder` | Write to `workflow_tasks` with scheduled follow-up |
| `log_farmer_action` | Record farmer-confirmed action as memory event |
| `compare_scenarios` | Side-by-side harvest timing / feed adjustment scenarios |

### Embeddings
- Replace `text-embedding-ada-002` with `text-embedding-3-large`
- Index: farm memories, cycle summaries, observation notes
- Store vectors in `pgvector` alongside source rows (no separate Pinecone namespace mismatch risk)

### Success criteria
- Chat answers are concise, cite real data rows, and end with a next action
- High-risk advice (chemical treatment, mortality event) includes uncertainty rating and escalation guidance
- Safety guard vetoes responses that assert chemical doses without verified expert input

---

## Phase 5 — Proactive Workflows
**Duration:** 3–5 weeks

### Closed-loop alert pattern

```
Condition detected (Celery Beat / TimescaleDB continuous aggregate)
  → FarmAlert created with follow_up_scheduled_at
  → Agent pushes explanation + recommendation to farmer
  → workflow_task created: "confirm aeration checked by [time]"
  → Farmer confirms or dismisses
  → Outcome stored as advice_history memory
  → Next reading checked; alert resolved or escalated
```

### Trigger conditions

| Condition | Threshold | Severity |
|-----------|-----------|---------|
| DO below optimal for 2 readings | < 4 mg/L | warning |
| DO below survival minimum | < 2 mg/L | critical |
| NH3 rising for 3 consecutive days | trend + absolute | warning |
| NH3 approaching limit | > 80% of suitable max | critical |
| Feed leftover above threshold | > 20% uneaten | info |
| Growth lag after DOC 45 | SGR < expected | warning |
| Harvest window within 7 days | optimal DOC − current DOC ≤ 7 | info |
| Cost/kg exceeding benchmark | > historical mean + 1σ | info |

### `FarmAlert` additions required
```
resolved_at: datetime (nullable)
resolution_note: text (nullable)
follow_up_scheduled_at: datetime (nullable)
follow_up_completed: bool
outcome_memory_id: FK → agent_memories (nullable)
```

### Temporal workflows (Phase 5+)
Use Temporal for:
- Multi-day follow-up chains ("check DO again in 24h")
- Harvest countdown reminders
- Scheduled weekly summaries
- "Watch pond X for 3 days" user-requested monitoring windows

### Success criteria
- Teramina moves from "dashboard you check" to "assistant that watches with you"
- Every generated alert has a resolution path — not just a dismiss button

---

## Phase 6 — Farmer UX
**Duration:** 3–4 weeks

### Mobile-first surfaces

**Today view**
- Urgent actions (unresolved critical alerts)
- Pond status grid (DO, temp, NH3 per active pond, RAG colored)
- Expected tasks for the day
- One-tap access to ask the assistant

**Chat drawer**
- Context-aware (knows current farm, pond, cycle from page)
- Quick-prompt chips change per page context
- Streaming responses via SSE
- Cites data inline: "DO was 3.1 mg/L at DOC 42 (yesterday)"

**Pond timeline**
- Chronological feed: readings, events, AI recommendations, farmer actions
- Expandable entries with source data
- Filter by type: water | feed | growth | advice | notes

**Voice note input**
- Record in Bahasa Indonesia
- Transcribe via Whisper
- Stored as `farmer_notes`, automatically parsed for memory extraction

**Offline-first daily log**
- Works with no connectivity
- Syncs when connection restored
- Required fields only: DO, temp, feed given, observations

**"Explain to team" button**
- Summarizes current pond status in simple Bahasa Indonesia
- Suitable for printing or sharing with farm workers

### PWA requirements
- Service worker for offline daily log
- Background sync for pending writes
- Push notifications for critical alerts (Web Push API)

### Success criteria
- Farmer can complete the daily log from a phone at pond-side with 2G connectivity
- Critical alert push notification arrives within 10 minutes of condition detected

---

## Phase 7 — Evaluation, Safety, and Trust
**Duration:** Ongoing from Phase 4

### AI evals

| Eval type | Method |
|-----------|--------|
| Factual accuracy | Golden Q&A set per farm/cycle; verify cited numbers match DB |
| Hallucination check | Any number in response must trace to a tool result |
| Tool-call accuracy | Known scenario → expected tool(s) called |
| Bahasa Indonesia quality | Native speaker review of 20 sample responses |
| Recommendation risk grading | High-risk advice flags reviewed by aquaculture expert |
| Regression tests | 10 critical farm scenarios (low DO, harvest timing, disease event) |

### Product safeguards (non-negotiable)
- "Data unavailable" must be stated explicitly — never inferred or fabricated
- Chemical/treatment recommendations require disclaimer: "Consult your aquaculture extension officer before applying."
- Every recommendation includes: reason, source data reference, confidence level
- Every alert includes: what triggered it, what the threshold is, what it means

---

## Suggested Timeline

| Phase | Duration | Cumulative |
|-------|----------|-----------|
| Phase 0: Audit | 1 week | 1 week |
| Phase 1: Foundation | 2–3 weeks | 4 weeks |
| Phase 2: Data Backbone | 3–5 weeks | 9 weeks |
| Phase 3: Memory | 3–4 weeks | 13 weeks |
| Phase 4: Agent Architecture | 4–6 weeks | 19 weeks |
| Phase 5: Proactive Workflows | 3–5 weeks | 24 weeks |
| Phase 6: Farmer UX | 3–4 weeks | 28 weeks |
| Phase 7: Evals/Safety | Ongoing | — |

**MVP second brain (Phases 0–3):** 10–12 weeks
**Farmer-ready beta (Phases 0–5):** 16–20 weeks
**Production-grade proactive copilot (all phases):** 24+ weeks

---

## Immediate Next Moves (this week)

Three surgical changes that unblock everything downstream:

### 1. Wire context into agent chat
File: `fe-teramina-main/src/components/agent-chat/queries.ts`
Change `useSendAgentMessage` to include `farm_id`, `pond_id`, `cycle_id` read from the `farm-management` store.

### 2. Fix `get_cost_breakdown` query bug
File: `core-be-teramina-main/teramina/agent/services/agent_tools.py:151`
Change `CostData.objects(farm_id=cycle_id)` to `CostData.objects(cycle_id=cycle_id)`.

### 3. Raise agent token limit and restore session history
File: `core-be-teramina-main/teramina/agent/services/agent_service.py:111`
Raise `max_tokens` from 1024 to 4096.
File: `fe-teramina-main/src/components/agent-chat/index.jsx`
On drawer open, fetch existing session messages from `GET /agent/session` and populate local state.

These three changes cost under 2 hours of work and make the existing agent functional before any Phase 1 migration begins.
