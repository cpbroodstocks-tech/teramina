# pylint: disable=missing-class-docstring

from mongoengine import Document, fields, QuerySetManager


class Variable(Document):
    data = fields.ListField(fields.StringField())

    # Define the objects manager
    objects = QuerySetManager()


class WQVariable(Document):
    name = fields.StringField()
    weight = fields.FloatField()
    type = fields.StringField()
    lower_bound = fields.FloatField()
    optimal_min = fields.FloatField()
    optimal_max = fields.FloatField()
    upper_bound = fields.FloatField()

    # Define the objects manager
    objects = QuerySetManager()
