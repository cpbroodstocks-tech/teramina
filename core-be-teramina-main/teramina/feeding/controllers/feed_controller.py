# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from ..schemas.feed_schema import FeedDataSchema, FeedUpdateSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ..services.feed_realization_service import FeedRealizationService
from ..services.feed_recommendation_service import FeedRecommendationService

router = Router(tags=["Feeding"])

code_schema = {
    200: DataSuccessSchema,
    400: DataErrorSchema,
    401: DataErrorSchema,
}


@router.post("/add-feeding", response=code_schema, auth=AuthBearer())
def add_feed_tray_data(
    request, cycle_id, data: FeedDataSchema = Body(...), number_of_ration: int = 4
):
    """
    Record a tray reading for one ration slot.
    number_of_ration: total ration slots configured for this cycle (1-10).
    feed_leftover in body is optional — omit if tray was not checked.
    """
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    max_ration = max(1, min(number_of_ration, 10))
    return FeedRealizationService(cycle_id, max_ration_number=max_ration).add_feed_data(data)


@router.put("/edit-feeding", response=code_schema, auth=AuthBearer())
def edit_feed_tray_data(
    request, cycle_id, ration_id, data: FeedUpdateSchema = Body(...)
):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FeedRealizationService(cycle_id).edit_feed_data(ration_id, data)


@router.get("/get-feeding", response=code_schema, auth=AuthBearer())
def get_feed_realization(request, cycle_id, date, number_of_ration: int = 4):
    """
    number_of_ration: how many ration slots to show (1-10).
    Slots with no recorded data will appear as empty.
    """
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    max_ration = max(1, min(number_of_ration, 10))
    return FeedRealizationService(cycle_id, max_ration_number=max_ration).get_feed_data(
        date, max_ration
    )


@router.get("/get-feed-recommendation", response=code_schema, auth=AuthBearer())
def get_feed_recommendation(request, cycle_id, date):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FeedRecommendationService(cycle_id).get_recommendation(date)


@router.delete("/delete-feed-realization", response=code_schema, auth=AuthBearer())
def delete_feed_realization(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FeedRealizationService(cycle_id).reset_all_feed()
