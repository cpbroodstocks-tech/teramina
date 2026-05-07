from datetime import datetime
from teramina.cycle.models.cycle_model import Cycle
from teramina.helpers.constant_value import Constant


def get_max_filter_doc(cycle_id, use_constant_handler=False, date=None):
    """get the maximum doc

    Args:
        cycle_id (str): id of a cycle.
        use_constant_handler (bool, optional): constant condition. Defaults to False.
        date (str, optional): filtered date. Defaults to None.

    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        int: DOC (daily of culture)
    """
    if use_constant_handler:
        return Constant.MAX_DOC

    # verify the cycle data
    cycle = Cycle.objects(id=cycle_id).only("start_date").first()
    if not cycle:
        raise ValueError(f"Cycle with id {cycle_id} doesn't exist")

    start_date = cycle.start_date

    if date:
        try:
            end_date = datetime.strptime(date, "%m/%d/%Y")
        except ValueError as exc:
            raise ValueError(f"Invalid date format: {date}") from exc
    else:
        end_date = datetime.now()

    days = (end_date - start_date).days + 1
    return days
