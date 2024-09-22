from marshmallow import Schema, fields


class TimeIntervalSchema(Schema):
    start = fields.Str(required=False)
    end = fields.Str(required=False)


class TimeIntervalWithBucketSchema(Schema):
    start = fields.Str(required=False)
    end = fields.Str(required=False)
    bucket = fields.Str(required=False)
