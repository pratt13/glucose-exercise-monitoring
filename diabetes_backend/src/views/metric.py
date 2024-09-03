import logging
from datetime import datetime as dt
from flask import request
from src.constants import DATABASE_DATETIME
from src.utils import convert_ts_to_str
from src.views.base import BaseView

logger = logging.getLogger("app")


class Metric(BaseView):
    """
    Retrieve the data within a range and compute a metric
    """

    def __init__(self, Schema, RecordModel, metric):
        self.schema = Schema
        self.model = RecordModel
        self.metric = metric

    def get(self):
        """
        Compute the metric from the data
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
        additional_request_args = create_additional_kwargs(
            request.args,
            list(self.schema.__dict__.get("declared_fields", {}).keys()),
            excluded_keys=("start", "end"),
        )
        logger.debug(f"Getting average glucose level from {start_time} to {end_time}")
        data = self.model.get_records(start_time, end_time)
        res = self.metric(data, **additional_request_args)
        logger.debug(f"Found {self.metric} in time range {start_time} - {end_time}")
        fmt_result = str(res) if isinstance(res, float) else res
        return fmt_result, 200


# TODO: Move to utils and test
def create_additional_kwargs(value_dict, keys, excluded_keys=None):
    res = {}
    if excluded_keys is None:
        excluded_keys = []
    for key in keys:
        value = value_dict.get(key)
        if value and key not in excluded_keys:
            res[key] = value
    logger.debug(f"Adding additional kwargs {res}")
    return res
