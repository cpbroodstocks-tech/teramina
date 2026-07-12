# pylint: disable=no-member
"""
Ownership verification helpers.
Each function returns True if the given user owns the resource, False otherwise.
Use these in controllers before mutating or reading user-specific resources.
"""

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from mongoengine.errors import ValidationError


def verify_farm_owner(farm_id: str, user_id: str) -> bool:
    """Return True if user_id owns farm_id."""
    try:
        return Farm.objects(id=farm_id, user_id=str(user_id)).only("id").first() is not None
    except (TypeError, ValidationError):
        return False


def verify_pond_owner(pond_id: str, user_id: str) -> bool:
    """Return True if user_id owns the farm that contains pond_id."""
    try:
        pond = Pond.objects(id=pond_id).only("farm_id").first()
    except (TypeError, ValidationError):
        return False
    if not pond:
        return False
    return verify_farm_owner(pond.farm_id, user_id)


def verify_cycle_owner(cycle_id: str, user_id: str) -> bool:
    """Return True if user_id owns the pond (and its farm) for cycle_id."""
    try:
        cycle = Cycle.objects(id=cycle_id).only("pond_id").first()
    except (TypeError, ValidationError):
        return False
    if not cycle:
        return False
    return verify_pond_owner(cycle.pond_id, user_id)
