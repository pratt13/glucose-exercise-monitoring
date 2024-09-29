import unittest
from unittest.mock import patch
from datetime import datetime as dt

import flask
from src.views.metric import Metric
from marshmallow import Schema, fields
from werkzeug import exceptions
from src.constants import STRAVA_DATETIME
from src.utils import (
    convert_ts_to_str,
)


class TestSchema(Schema):
    start = fields.Str(required=False)
    end = fields.Str(required=True)


class TestSchemaAdditionalKwargs(Schema):
    start = fields.Str(required=False)
    end = fields.Str(required=True)
    additional_value = fields.Float(required=False)


def test_func(data, idx, additional_value=0):
    """
    Test function to increment the value by 1
    """
    return list(map(lambda x: x[idx] + 1 + additional_value, data))


class TestUtils(unittest.TestCase):
    @patch("src.glucose_new.GlucoseManager")
    def test_get_glucose_success(self, mock_glucose):
        """Test for the get for glucose, but we are only really making use of it for spec-ing."""
        flask_app = flask.Flask("test_flask_app")
        with flask_app.test_request_context() as mock_context:
            mock_context.request.args = {
                "start": convert_ts_to_str(dt(2000, 1, 1), STRAVA_DATETIME),
                "end": convert_ts_to_str(dt(2001, 1, 1), STRAVA_DATETIME),
            }
            mock_glucose.get_records_between_timestamp.return_value = [
                [1, 2],
                [2, 2],
                [3, 2],
            ]
            metric = Metric(
                TestSchema(),
                mock_glucose,
                lambda x, **kwargs: test_func(x, 0, **kwargs),
            )
            result = metric.get()
            self.assertEqual(result, ([2, 3, 4], 200))

    @patch("src.glucose_new.GlucoseManager")
    def test_get_glucose_success_additional_kwargs(self, mock_glucose):
        """Test for the get for glucose, but we are only really making use of it for spec-ing."""
        flask_app = flask.Flask("test_flask_app")
        with flask_app.test_request_context() as mock_context:
            mock_context.request.args = {
                "start": convert_ts_to_str(dt(2000, 1, 1), STRAVA_DATETIME),
                "end": convert_ts_to_str(dt(2001, 1, 1), STRAVA_DATETIME),
                "additional_value": 0.5,
            }
            mock_glucose.get_records_between_timestamp.return_value = [
                [1, 2],
                [2, 2],
                [3, 2],
            ]
            metric = Metric(
                TestSchemaAdditionalKwargs(),
                mock_glucose,
                lambda x, **kwargs: test_func(x, 0, **kwargs),
            )
            result = metric.get()
            self.assertEqual(result, ([2.5, 3.5, 4.5], 200))

    @patch("src.glucose_new.GlucoseManager")
    def test_get_glucose_fail_schema(self, mock_glucose):
        """Test for the get for glucose, but we are only really making use of it for spec-ing."""
        flask_app = flask.Flask("test_flask_app")
        with flask_app.test_request_context() as mock_context:
            metric = Metric(TestSchema(), mock_glucose, lambda x: test_func(x, 0))
            mock_context.request.args = {
                "start": convert_ts_to_str(dt(2000, 1, 1), STRAVA_DATETIME)
            }
            with self.assertRaises(exceptions.BadRequest) as e:
                metric.get()
            self.assertEqual(
                str(e.exception),
                "400 Bad Request: {'end': ['Missing data for required field.']}",
            )
