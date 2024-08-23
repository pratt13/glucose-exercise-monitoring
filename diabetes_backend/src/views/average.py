import logging
from datetime import datetime as dt
from flask import request
from src.constants import DATABASE_DATETIME
from src.utils import compute_time_series_average, convert_ts_to_str
from src.views.base import BaseView

logger = logging.getLogger("app")


class AverageGlucose(BaseView):
    """
    Retrieve the average Glucose of the data
    """

    def __init__(self, Schema, RecordModel):
        self.schema = Schema
        self.model = RecordModel

    def get(self):
        """
        Get the average for the metric.
        It is validated against the corresponding schema in schema.py.
        If no end time is provided it defaults to now.
        If no start time is provided it defaults to the earliest possible.
        """
        logger.debug("Getting average glucose level")
        self.validate_against_schema(self.schema, request.args)
        default_start_time = convert_ts_to_str(dt(1900, 1, 1), DATABASE_DATETIME)
        default_end_time = convert_ts_to_str(dt.now(), DATABASE_DATETIME)
        start_time = request.args.get("start", default_start_time)
        end_time = request.args.get("end", default_end_time)
        logger.debug(f"Getting average glucose level from {start_time} to {end_time}")
        res = self.model.get_records(start_time, end_time)
        av = compute_time_series_average(res)
        logger.debug(
            f"Found average glucose to be {av} in time range {start_time} - {end_time}"
        )
        return str(av), 200
