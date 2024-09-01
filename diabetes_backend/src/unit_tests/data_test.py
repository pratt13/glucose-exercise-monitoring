import os
import unittest
from unittest.mock import patch
from datetime import datetime
from requests import HTTPError
from src.data import Data
from src.constants import DATA_TYPES, TABLE_SCHEMA


ERROR_MSG = "My test error"


class MockRequest:
    def __init__(self, data, raise_error=False):
        self.data = data
        self.raise_error = raise_error

    def json(self):
        return {"data": self.data}

    def raise_for_status(self):
        if self.raise_error:
            raise HTTPError(ERROR_MSG)


POSTGRES_ENV = {
    "DB_HOST": "host",
    "DB_USERNAME": "user",
    "DB_NAME": "dbname",
    "DB_PASSWORD": "password",
}


@patch.dict(
    os.environ,
    POSTGRES_ENV,
    clear=True,
)
class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mock_strava_data = [
            f"STRAVA_{col}" for col in TABLE_SCHEMA.COLUMNS[DATA_TYPES.STRAVA]
        ]
        # REplace the mock data dt objects to 5/6
        cls.mock_strava_data[5] = datetime(2000, 1, 1)
        cls.mock_strava_data[6] = datetime(2000, 2, 1)

    @patch("database_manager.PostgresManager")
    def test_save_data(self, mock_database_manager):
        data = Data(mock_database_manager)
        # No data
        data._save_data([])
        self.assertEqual(mock_database_manager.save_data.call_count, 0)
        # Some data data
        data._save_data([1, 2])
        mock_database_manager.save_data.assert_called_once()
        mock_database_manager.save_data.assert_called_with(
            [1, 2], DATA_TYPES.STRAVA_LIBRE
        )

    @patch("database_manager.PostgresManager")
    def test_get_last_record(self, mock_database_manager):
        data = Data(mock_database_manager)
        # Some data data
        data._get_last_record()
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(
            DATA_TYPES.STRAVA_LIBRE
        )

    @patch("database_manager.PostgresManager")
    def test_get_glucose_records_within_interval(self, mock_database_manager):
        data = Data(mock_database_manager)
        # Some data data
        data._get_glucose_records_within_interval(
            datetime(2000, 1, 1), datetime(2000, 2, 1)
        )
        mock_database_manager.get_records.assert_called_once()
        mock_database_manager.get_records.assert_called_with(
            DATA_TYPES.LIBRE, datetime(2000, 1, 1), datetime(2000, 2, 1)
        )

    @patch("database_manager.PostgresManager")
    def test_combine_data_no_strava_data(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = [
            1,
            2,
            3,
        ]  # Mock get last record, value doesn't matter just needs length 3
        mock_database_manager.get_filtered_by_id_records.return_value = (
            []
        )  # Mock get_filtered_by_id_records to be empty
        data = Data(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(
            DATA_TYPES.STRAVA_LIBRE
        )
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            DATA_TYPES.STRAVA, 3
        )
        # No data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 0)

    @patch("database_manager.PostgresManager")
    def test_combine_data_no_libre_data(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = [
            1,
            2,
            3,
        ]  # Mock get last record, value doesn't matter just needs length 3
        mock_strava_data = [
            f"STRAVA_{col}" for col in TABLE_SCHEMA.COLUMNS[DATA_TYPES.STRAVA]
        ]
        # REplace the mock data dt objects to 5/6
        mock_strava_data[5] = datetime(2000, 1, 1)
        mock_strava_data[6] = datetime(200, 2, 1)
        mock_database_manager.get_filtered_by_id_records.return_value = [
            mock_strava_data,
            mock_strava_data,
        ]  # Mock get_filtered_by_id_records to be two records
        mock_database_manager.get_records.return_value = (
            []
        )  # Mock libre data to be empty
        data = Data(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(
            DATA_TYPES.STRAVA_LIBRE
        )
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            DATA_TYPES.STRAVA, 3
        )
        self.assertEqual(mock_database_manager.get_records.call_count, 2)
        # No data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 0)

    @patch("database_manager.PostgresManager")
    def test_combine_data_success(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = [
            datetime(2000, 1, 10),
            1,
            3,
        ]  # Mock get last record, value doesn't matter just needs length 3
        mock_database_manager.get_filtered_by_id_records.return_value = [
            self.mock_strava_data
        ]  # Mock get_filtered_by_id_records to be single record
        mock_database_manager.get_records.return_value = [
            (1, 2, datetime(2000, 1, 10)),
            (4, 6, datetime(2000, 1, 20)),
        ]  # Mock libre data, can be anything as long as its length 3
        data = Data(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(
            DATA_TYPES.STRAVA_LIBRE
        )
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            DATA_TYPES.STRAVA, 3
        )
        self.assertEqual(mock_database_manager.get_records.call_count, 1)
        # Data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 1)
        mock_database_manager.save_data.assert_called_with(
            [
                (
                    2,
                    "STRAVA_id",
                    1,
                    2,
                    datetime(2000, 1, 10, 0, 0),
                    datetime(2000, 1, 1, 0, 0),
                    datetime(2000, 2, 1, 0, 0),
                    "STRAVA_activity_type",
                    781200.0,
                ),
                (
                    3,
                    "STRAVA_id",
                    4,
                    6,
                    datetime(2000, 1, 20, 0, 0),
                    datetime(2000, 1, 1, 0, 0),
                    datetime(2000, 2, 1, 0, 0),
                    "STRAVA_activity_type",
                    1645200.0,
                ),
            ],
            DATA_TYPES.STRAVA_LIBRE,
        )
