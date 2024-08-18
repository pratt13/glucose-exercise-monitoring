import logging
from flask import abort
from flask.views import MethodView
from datetime import datetime as dt
from src.constants import DATETIME_FORMAT


logger = logging.getLogger("app")


class BaseView(MethodView):
    def validate_against_schema(self, schema, args):
        errors = schema.validate(args)
        if errors:
            logger.error(errors)
            abort(400, str(errors))

    def convert_to_datetime(self, date_str):
        return dt.strptime(date_str, DATETIME_FORMAT)
