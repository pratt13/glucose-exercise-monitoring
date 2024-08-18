import logging
from datetime import datetime as dt
from flask import request
from src.constants import DATABASE_DATETIME
from src.utils import convert_ts_to_str
from src.views.base import BaseView

logger = logging.getLogger("app")


class RawData(BaseView):
    """
    Retrieve all the raw data from the model
    """

    def __init__(self, Schema, RecordModel):
        self.schema = Schema
        self.model = RecordModel

    def get(self):
        """
        Get the raw data for a given time window passed via params.
        It is validated against the corresponding schema in schema.py.
        If no end time is provided it defaults to now.
        If no start time is provided it defaults to the earliest possible.
        """
        logger.debug(f"Getting {self.model.name} Records")
        self.validate_against_schema(self.schema, request.args)
        default_start_time = convert_ts_to_str(dt(1900, 1, 1), DATABASE_DATETIME)
        default_end_time = convert_ts_to_str(dt.now(), DATABASE_DATETIME)
        start_time = request.args.get("start", default_start_time)
        end_time = request.args.get("end", default_end_time)
        logger.debug(
            f"Getting {self.model.name} Records from {start_time} to {end_time}"
        )
        res = self.model.get_records(start_time, end_time)
        logger.debug(f"Found {len(res)} in time range {start_time} - {end_time}")
        return res, 200
