# pylint: disable=no-member
"""
Ownership verification helpers.
Each function returns True if the given user owns the resource, False otherwise.
Use these in controllers before mutating or reading user-specific resources.
"""

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle


def verify_farm_owner(farm_id: str, user_id: str) -> bool:
    """Return True if user_id owns farm_id."""
    return Farm.objects(id=farm_id, user_id=str(user_id)).only("id").first() is not None


def verify_pond_owner(pond_id: str, user_id: str) -> bool:
    """Return True if user_id owns the farm that contains pond_id."""
    pond = Pond.objects(id=pond_id).only("farm_id").first()
    if not pond:
        return False
    return verify_farm_owner(pond.farm_id, user_id)


def verify_cycle_owner(cycle_id: str, user_id: str) -> bool:
    """Return True if user_id owns the pond (and its farm) for cycle_id."""
    cycle = Cycle.objects(id=cycle_id).only("pond_id").first()
    if not cycle:
        return False
    return verify_pond_owner(cycle.pond_id, user_id)
