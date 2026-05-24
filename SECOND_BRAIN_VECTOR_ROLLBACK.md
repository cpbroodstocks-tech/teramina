# Teramina Second Brain Vector Retrieval Rollback

## Scope

This rollback plan covers the Mongo MVP vector retrieval layer:

Product alignment comes from `CYBERNETIC_PRODUCT_FRAMEWORK.md`: retrieval is only valuable when it improves state interpretation, uncertainty handling, and follow-up decisions. If semantic retrieval weakens trust or scope safety, lexical/recent retrieval is preferable for beta.

- `memory_embeddings` companion collection.
- `backfill_agent_memory_graph --apply` indexing side effect.
- `search_farm_memory` semantic retrieval with lexical fallback.
- Chat context injection from `semantic_search_memories`.

## Safe Rollback Path

1. Stop writing new embeddings.
   - Remove or disable calls to `index_agent_memory` and `index_memory_observation`.
   - Keep flat `agent_memories` and `memory_observations` untouched.

2. Force lexical/recent retrieval.
   - Change `search_farm_memory` and `_build_memory_context` to read directly from `AgentMemory` and `MemoryObservation`, or make `semantic_search_memories` skip `MemoryEmbedding` reads.
   - This preserves farmer-visible behavior, with only relevance ranking reduced.

3. Leave `memory_embeddings` in place initially.
   - The collection is derived data.
   - Do not delete it during emergency rollback; deleting is unnecessary for app correctness.

4. Rebuild later if needed.
   - Run `python manage.py backfill_agent_memory_graph --apply` to regenerate graph links and embeddings after the fix.

## Emergency Disable Criteria

Disable semantic retrieval if any of these occur:

- Memory search latency materially degrades chat response time.
- Search results return memories outside the active farm or pond scope.
- Embeddings become stale after memory edits or deletes.
- Chat responses cite memory refs that no longer exist.

## Verification After Rollback

Run:

```bash
pytest tests/test_agent_memory.py
python manage.py check
```

Then smoke-test:

- Memory page loads.
- Pond memory panel loads.
- Chat drawer can answer with current farm/pond/cycle context.

## Data Safety

`memory_embeddings` is disposable derived data. The source of truth remains:

- `agent_memories`
- `memory_observations`
- `memory_entities`
- `memory_relations`
