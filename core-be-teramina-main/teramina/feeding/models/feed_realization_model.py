# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager

class FeedRealization(Document):
    cycle_id = fields.StringField()
    doc = fields.IntField()
    ration_number = fields.IntField()
    feed_ration = fields.FloatField()
    feed_given = fields.FloatField()
    feed_leftover = fields.FloatField()
    last_updated = fields.DateTimeField(default=datetime.now())

    # Define the objects manager
    objects = QuerySetManager()

# """
# ration_data = {
#     "ration1": {
#         "realized_feed_given": "",
#         "realized_feed_ration": "",
#         "left_over": ""
#     },
#     "ration2": {
#         "realized_feed_given": "",
#         "realized_feed_ration": "",
#         "left_over": ""
#     },
#     "ration3": {
#         "realized_feed_given": "",
#         "realized_feed_ration": "",
#         "left_over": ""
#     },
#     "ration4": {
#         "realized_feed_given": "",
#         "realized_feed_ration": "",
#         "left_over": ""
#     }
# }
# """
