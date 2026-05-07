from ninja.errors import ValidationError
from mongoengine.errors import InvalidQueryError
from ..models.cycle_model import Data

def cycle_validation(cycle_id):
    """verify wether cycle exists or not"""
    try:
        data = Data.objects(cycle_id=cycle_id).first()
        if data:
            raise ValidationError("data was existed in this cycle")

    except InvalidQueryError as exc:
        raise InvalidQueryError("Query Error") from exc
