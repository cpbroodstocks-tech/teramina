# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class HarvestRecommendation(Document):
    cycle_id = fields.StringField()
    harvest_data = fields.DictField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()


# {
#     "harvest_data": {
#         "data": [
#             {
#                 "type": "partial",
#                 "partial_number": "1",
#                 "doc": "",
#                 "value": ""
#             },
#             {
#                 "type": "final",
#                 "partial_number": None,
#                 "doc": "",
#                 "value": ""
#             }
#         ]
#     }
# }
