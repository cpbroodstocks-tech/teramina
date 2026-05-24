"""Scoped memory retrieval for MongoEngine-backed Mnemon memory."""

import hashlib
import logging
import math
import re
import time
from datetime import datetime

from teramina.agent.models.agent_model import AgentMemory, MemoryEmbedding, MemoryObservation
from teramina.agent.services.embedding import get_embedding

logger = logging.getLogger("teramina")

# Kept for test injection — deterministic 64-dim hash embedding.
DEFAULT_EMBEDDING_MODEL = "teramina-local-hash-v1"
EMBEDDING_DIMENSIONS = 64


def _clamp_confidence(value):
    if value is None:
        return 0.7
    return max(0.0, min(1.0, float(value)))


def _content_hash(content):
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


def _tokenize(text):
    return [t for t in re.findall(r"[a-zA-Z0-9_]+", (text or "").lower()) if len(t) > 1]


def _cosine_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    ln = math.sqrt(sum(a * a for a in left))
    rn = math.sqrt(sum(b * b for b in right))
    if not ln or not rn:
        return 0.0
    return dot / (ln * rn)


def _normalize_embedding(value):
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    return value if isinstance(value, list) else []


def _lexical_score(query, content, tags=None):
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return 0.0
    content_tokens = set(_tokenize(content))
    tag_tokens = set()
    for tag in tags or []:
        tag_tokens.update(_tokenize(tag))
    matched = query_tokens & (content_tokens | tag_tokens)
    return len(matched) / len(query_tokens)


class LocalHashEmbeddingProvider:
    """Deterministic 64-dim embedding for tests and offline use."""

    model = DEFAULT_EMBEDDING_MODEL

    def embed(self, texts):
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text):
        vector = [0.0] * EMBEDDING_DIMENSIONS
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector))
        if not norm:
            return vector
        return [v / norm for v in vector]


def index_agent_memory(memory, provider=None):
    """Write/update an embedding sidecar for an AgentMemory document."""
    emb = _normalize_embedding(provider.embed([memory.content])[0] if provider is not None else get_embedding(memory.content))
    if not emb:
        provider = LocalHashEmbeddingProvider()
        emb = provider.embed([memory.content])[0]
    if not emb:
        return memory, False
    source_ref = f"agent_memory:{memory.id}"
    MemoryEmbedding.objects(source_ref=source_ref).update_one(
        set__user_id=memory.user_id,
        set__farm_id=memory.farm_id or "",
        set__pond_id=memory.pond_id or "",
        set__cycle_id=memory.cycle_id or "",
        set__source_kind="agent_memory",
        set__content=memory.content,
        set__embedding=emb,
        set__embedding_model=getattr(provider, "model", DEFAULT_EMBEDDING_MODEL),
        set__content_hash=_content_hash(memory.content),
        set__confidence=_clamp_confidence(memory.confidence),
        set__is_verified=memory.is_verified,
        set__updated_at=datetime.utcnow(),
        set_on_insert__created_at=datetime.utcnow(),
        upsert=True,
    )
    memory.embedding = emb
    memory.updated_at = datetime.utcnow()
    memory.save()
    return memory, True


def index_memory_observation(observation, provider=None):
    """Write/update an embedding sidecar for a MemoryObservation document."""
    emb = _normalize_embedding(provider.embed([observation.content])[0] if provider is not None else get_embedding(observation.content))
    if not emb:
        provider = LocalHashEmbeddingProvider()
        emb = provider.embed([observation.content])[0]
    if not emb:
        return observation, False
    source_ref = f"memory_observation:{observation.id}"
    MemoryEmbedding.objects(source_ref=source_ref).update_one(
        set__user_id=observation.user_id,
        set__farm_id=observation.farm_id or "",
        set__pond_id=observation.pond_id or "",
        set__cycle_id=observation.cycle_id or "",
        set__source_kind="memory_observation",
        set__content=observation.content,
        set__embedding=emb,
        set__embedding_model=getattr(provider, "model", DEFAULT_EMBEDDING_MODEL),
        set__content_hash=_content_hash(observation.content),
        set__confidence=_clamp_confidence(observation.confidence),
        set__is_verified=observation.is_verified,
        set__updated_at=datetime.utcnow(),
        set_on_insert__created_at=datetime.utcnow(),
        upsert=True,
    )
    return observation, True


def index_memory_record(record, provider=None):
    if isinstance(record, AgentMemory):
        return index_agent_memory(record, provider)
    if isinstance(record, MemoryObservation):
        return index_memory_observation(record, provider)
    raise TypeError(f"Unsupported memory record type: {type(record)}")


def _serialize_flat_memory(memory, score=0.0):
    tags = list(memory.tags) if memory.tags else []
    return {
        "type": memory.memory_type,
        "content": memory.content,
        "tags": tags,
        "pond_id": memory.pond_id or None,
        "cycle_id": memory.cycle_id or None,
        "source": memory.source,
        "confidence": _clamp_confidence(memory.confidence),
        "is_verified": memory.is_verified,
        "created_at": memory.created_at.isoformat() if memory.created_at else None,
        "source_ref": f"agent_memory:{memory.id}",
        "score": round(score, 4),
    }


def _serialize_observation(observation, score=0.0):
    return {
        "type": observation.observation_type,
        "content": observation.content,
        "tags": [],
        "pond_id": observation.pond_id or None,
        "cycle_id": observation.cycle_id or None,
        "source": observation.source_type,
        "confidence": _clamp_confidence(observation.confidence),
        "is_verified": observation.is_verified,
        "created_at": observation.created_at.isoformat() if observation.created_at else None,
        "source_ref": f"memory_observation:{observation.id}",
        "score": round(score, 4),
    }


def _base_filters(user_id, farm_id, pond_id):
    filters = {"farm_id": farm_id}
    if user_id:
        filters["user_id"] = user_id
    if pond_id:
        filters["pond_id"] = pond_id
    return filters


def _fallback_rank(query, filters, limit):
    rows = []
    memories = list(AgentMemory.objects(**filters).order_by("-created_at")[: limit * 4])
    observations = list(MemoryObservation.objects(**filters).order_by("-created_at")[: limit * 4])
    for memory in memories:
        tags = list(memory.tags) if memory.tags else []
        lexical = _lexical_score(query, memory.content, tags)
        score = lexical + (_clamp_confidence(memory.confidence) * 0.05) + (0.05 if memory.is_verified else 0.0)
        rows.append((score, _serialize_flat_memory(memory, score)))
    for obs in observations:
        lexical = _lexical_score(query, obs.content)
        score = lexical + (_clamp_confidence(obs.confidence) * 0.05) + (0.05 if obs.is_verified else 0.0)
        rows.append((score, _serialize_observation(obs, score)))
    rows.sort(key=lambda item: (item[0], item[1].get("created_at") or ""), reverse=True)
    return [row for score, row in rows if score > 0][:limit] or [row for _, row in rows[:limit]]


def semantic_search_memories(farm_id, query="", pond_id="", user_id="", limit=10, provider=None):
    started_at = time.perf_counter()
    filters = _base_filters(user_id, farm_id, pond_id)
    query = query or ""
    retrieval = "recent"
    rows = []

    if query:
        query_emb = _normalize_embedding(provider.embed([query])[0] if provider is not None else get_embedding(query))
        if not query_emb:
            provider = LocalHashEmbeddingProvider()
            query_emb = provider.embed([query])[0]

        if query_emb:
            embedding_filters = {key: value for key, value in filters.items() if value}
            embedding_filters["source_kind"] = "agent_memory"
            embeddings = list(MemoryEmbedding.objects(**embedding_filters))
            ranked = sorted(
                [
                    (_cosine_similarity(query_emb, embedding.embedding), embedding)
                    for embedding in embeddings
                    if embedding.embedding
                ],
                key=lambda item: item[0],
                reverse=True,
            )
            source_refs = [embedding.source_ref for _, embedding in ranked[:limit]]
            if source_refs:
                memory_ids = [ref.split(":", 1)[1] for ref in source_refs if ref.startswith("agent_memory:")]
                memories_by_id = {
                    str(memory.id): memory
                    for memory in AgentMemory.objects(id__in=memory_ids)
                }
                retrieval = "semantic"
                rows = [
                    _serialize_flat_memory(memories_by_id[memory_id], score)
                    for score, embedding in ranked[:limit]
                    for memory_id in [embedding.source_ref.split(":", 1)[1]]
                    if memory_id in memories_by_id
                ]
                _log_search(farm_id, pond_id, retrieval, len(rows), started_at)
                return {"farm_id": farm_id, "count": len(rows), "memories": rows, "retrieval": retrieval}

        # Lexical fallback
        retrieval = "lexical_fallback"
        rows = _fallback_rank(query, filters, limit)
        _log_search(farm_id, pond_id, retrieval, len(rows), started_at)
        return {"farm_id": farm_id, "count": len(rows), "memories": rows, "retrieval": retrieval}

    # No query — return most recent memories
    memories = list(AgentMemory.objects(**filters).order_by("-created_at")[:limit])
    rows = [_serialize_flat_memory(m) for m in memories]
    _log_search(farm_id, pond_id, retrieval, len(rows), started_at)
    return {"farm_id": farm_id, "count": len(rows), "memories": rows, "retrieval": retrieval}


def _log_search(farm_id, pond_id, retrieval, count, started_at):
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "memory_search farm_id=%s pond_id=%s retrieval=%s count=%s elapsed_ms=%s",
        farm_id, pond_id or "", retrieval, count, elapsed_ms,
    )
