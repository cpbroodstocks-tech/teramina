"""
Management command: backfill_agent_memory_graph
------------------------------------------------
Synchronizes existing flat AgentMemory documents with graph MemoryObservation
documents before semantic/vector retrieval is enabled.

Usage:
    python manage.py backfill_agent_memory_graph
    python manage.py backfill_agent_memory_graph --apply
    python manage.py backfill_agent_memory_graph --farm-id <farm_id> --apply
"""

from django.core.management.base import BaseCommand

from teramina.agent.models.agent_model import AgentMemory, MemoryObservation
from teramina.agent.services.memory_retrieval import index_agent_memory, index_memory_observation
from teramina.agent.services.agent_tools import _store_memory_observation


DEFAULT_CONFIDENCE = 0.7


def _clamp_confidence(value):
    if value is None:
        return DEFAULT_CONFIDENCE
    return max(0.0, min(1.0, float(value)))


def _source_type_for_memory(memory):
    if memory.source == "user_input":
        return "farmer"
    return "ai_inference"


def _matching_legacy_observations(memory):
    return list(
        MemoryObservation.objects(
            user_id=memory.user_id,
            farm_id=memory.farm_id or "",
            pond_id=memory.pond_id or "",
            cycle_id=memory.cycle_id or "",
            content=memory.content,
            source_ref="",
        ).order_by("-created_at")
    )


def _normalize_memory_confidence(memory, apply):
    normalized = _clamp_confidence(memory.confidence)
    if memory.confidence == normalized:
        return False
    if apply:
        memory.confidence = normalized
        memory.save()
    return True


def _normalize_observation_confidence(observation, apply):
    normalized = _clamp_confidence(observation.confidence)
    if observation.confidence == normalized:
        return False
    if apply:
        observation.confidence = normalized
        observation.save()
    return True


def backfill_agent_memory_graph(apply=False, user_id="", farm_id=""):
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if farm_id:
        filters["farm_id"] = farm_id

    stats = {
        "memories_scanned": 0,
        "observations_created": 0,
        "observations_linked": 0,
        "memories_normalized": 0,
        "observations_normalized": 0,
        "already_linked": 0,
        "duplicate_legacy_observations": 0,
    }

    for memory in AgentMemory.objects(**filters):
        stats["memories_scanned"] += 1
        if _normalize_memory_confidence(memory, apply):
            stats["memories_normalized"] += 1
        if apply:
            index_agent_memory(memory)

        source_ref = f"agent_memory:{memory.id}"
        linked_observation = MemoryObservation.objects(user_id=memory.user_id, source_ref=source_ref).first()

        if linked_observation:
            stats["already_linked"] += 1
            continue

        legacy_observations = _matching_legacy_observations(memory)
        if legacy_observations:
            observation = legacy_observations[0]
            if apply:
                observation.source_ref = source_ref
                observation.source_type = _source_type_for_memory(memory)
                observation.is_verified = memory.is_verified
                observation.confidence = _clamp_confidence(memory.confidence)
                observation.save()
                index_memory_observation(observation)
            stats["observations_linked"] += 1
            if len(legacy_observations) > 1:
                stats["duplicate_legacy_observations"] += len(legacy_observations) - 1
            continue

        if apply:
            observation = _store_memory_observation(
                user_id=memory.user_id,
                farm_id=memory.farm_id or "",
                pond_id=memory.pond_id or "",
                cycle_id=memory.cycle_id or "",
                memory_type=memory.memory_type,
                content=memory.content,
                source_type=_source_type_for_memory(memory),
                is_verified=memory.is_verified,
                source_ref=source_ref,
            )
            observation.confidence = _clamp_confidence(memory.confidence)
            observation.expires_at = memory.expires_at
            observation.save()
            index_memory_observation(observation)
        stats["observations_created"] += 1

    observation_filters = {}
    if user_id:
        observation_filters["user_id"] = user_id
    if farm_id:
        observation_filters["farm_id"] = farm_id

    for observation in MemoryObservation.objects(**observation_filters):
        if _normalize_observation_confidence(observation, apply):
            stats["observations_normalized"] += 1

    return stats


class Command(BaseCommand):
    help = "Backfill graph memory observations and source refs from flat AgentMemory documents"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually write changes (default is dry-run)",
        )
        parser.add_argument("--user-id", default="", help="Limit backfill to one user")
        parser.add_argument("--farm-id", default="", help="Limit backfill to one farm")

    def handle(self, *args, **options):
        apply = options["apply"]
        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(f"Mode: {mode}")

        stats = backfill_agent_memory_graph(
            apply=apply,
            user_id=options["user_id"],
            farm_id=options["farm_id"],
        )

        for key, value in stats.items():
            self.stdout.write(f"{key}: {value}")

        if not apply:
            self.stdout.write("Re-run with --apply to write changes.")
