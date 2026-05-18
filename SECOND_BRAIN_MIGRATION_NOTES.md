# Teramina Second Brain Migration And Backfill Notes

## Scope

These notes cover the MongoDB second-brain MVP before vector retrieval work starts.
They are for existing deployments that may already contain `agent_memories`,
`memory_observations`, `memory_entities`, and `memory_relations` documents.

## Current Document Sets

- `agent_memories`: flat farmer-visible memories.
- `memory_entities`: graph nodes for farms, ponds, cycles, and memory targets.
- `memory_relations`: graph links between entities.
- `memory_observations`: graph-attached memory text.

## Required Backfill

1. Backfill missing graph observations for existing `agent_memories`.
   - For every `agent_memories` document without a matching observation, create one through `_store_memory_observation`.
   - Use the flat memory fields: `user_id`, `farm_id`, `pond_id`, `cycle_id`, `memory_type`, and `content`.
   - Set `source_type` to `farmer` when `source == "user_input"`, otherwise use `ai_inference`.
   - Set `is_verified` from the flat memory.
   - Set `source_ref` to `agent_memory:<memory_id>`.

2. Backfill `source_ref` on matching legacy `memory_observations`.
   - Match by `user_id`, `farm_id`, `pond_id`, `cycle_id`, and exact `content`.
   - Only update observations where `source_ref` is empty.
   - If multiple observations match, keep the newest and mark older duplicates for review or deletion.

3. Normalize confidence values.
   - Clamp `AgentMemory.confidence` and `MemoryObservation.confidence` to `0.0 <= confidence <= 1.0`.
   - If confidence is missing, use `0.7`.

4. Verify lifecycle sync.
   - Deleting a flat memory must remove the observation with `source_ref == agent_memory:<memory_id>`.
   - Legacy fallback cleanup still removes exact matching observations without `source_ref`.

## Safety Rules

- Do not infer new memories during backfill.
- Do not overwrite farmer-verified content.
- Do not create duplicate observations when an observation already has the correct `source_ref`.
- Run backfill in batches and log counts for created, updated, skipped, and duplicate records.

## Pre-Vector Search Gate

Vector retrieval should not start until:

- Flat memory CRUD is stable.
- Graph observation lifecycle is synced with flat memory lifecycle.
- `source_ref` exists for current and backfilled memory observations.
- Controller/API tests pass for memory list, create, graph, and delete endpoints.
- The Memory page can show flat memories and graph observations for the active farm/pond context.
