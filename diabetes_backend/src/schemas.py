from marshmallow import Schema, fields


class GlucoseSchema(Schema):
    start = fields.Str(required=False)
    end = fields.Str(required=False)
