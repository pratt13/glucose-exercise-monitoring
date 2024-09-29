import unittest
from unittest.mock import patch
from requests import HTTPError
from datetime import datetime
from src.base_new import BaseNew
from src.utils import compute_epoch
from src.constants import DATA_TYPES, STRAVA_BASE_URL
from src.strava import StravaManager

ERROR_MSG = "My test error"


class ExampleBase(BaseNew):
    """ "
    Class to test the base functionality
    """

    @property
    def name(self):
        return "TEST"

    @property
    def table(self):
        return "test"


class MockRequest:
    def __init__(self, response, raise_error=False):
        self.response = response
        self.raise_error = raise_error

    def json(self):
        return self.response

    def raise_for_status(self):
        if self.raise_error:
            raise HTTPError(ERROR_MSG)


class TestBase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.client_id = "myId"
        self.client_secret = "secret"
        self.refresh_token = "my_token"
        self.code = "my_code"
        self.start_time = "2020-01-01T12:05:02Z"
        self.end_time = "2020-01-01 12:05:10"
        # Test data sample - we skip some records for brevity
        self.test_data_1 = {
            "id": "1",
            "athlete": {"id": "123"},
            "distance": 105,
            "type": "Run",
            "moving_time": 6,
            "elapsed_time": 8,
            "start_date": self.start_time,
            "start_latlng": [4.4, 6.2],
            "end_latlng": [5.5, 7.1],
        }
        self.start_date = "01/01/2021"
        self.end_date = "01/01/2022"
        self.expected_formatted_data = {
            "id": "1231",
            "distance": 105,
            "activity_type": "Run",
            "moving_time": 6,
            "elapsed_time": 8,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start_latitude": 4.4,
            "end_latitude": 5.5,
            "start_longitude": 6.2,
            "end_longitude": 7.1,
        }

    @patch("src.database_manager_new.DatabaseManager")
    def test_get_records_between_timestamp(self, mock_database_manager):
        mock_database_manager.get_records_between_timestamp.return_value = [
            [1, 2, 3],
            [4, 5, 6],
        ]
        base_cls = ExampleBase(
            mock_database_manager,
        )
        result = base_cls.get_records_between_timestamp(self.start_date, self.end_date)
        self.assertEqual(
            result,
            [[1, 2, 3], [4, 5, 6]],
        )

    @patch("src.database_manager_new.DatabaseManager")
    def test_get_last_record(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = 123
        base_cls = ExampleBase(
            mock_database_manager,
        )
        self.assertEqual(123, base_cls._get_last_record())
        mock_database_manager.get_last_record.assert_called_once_with(base_cls.table)

    @patch("src.database_manager_new.DatabaseManager")
    def test_save_data(self, mock_database_manager):
        base_cls = ExampleBase(
            mock_database_manager,
        )
        # Nothing to save
        base_cls._save_data([])
        mock_database_manager.save_data.assert_not_called()
        # Nothing to save
        base_cls._save_data([1, 2])
        mock_database_manager.save_data.assert_called_once_with([1, 2])
