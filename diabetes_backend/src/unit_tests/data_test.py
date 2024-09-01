import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from requests import HTTPError
from src.database.tables import Glucose, GlucoseExercise, Strava
from src.data import DataManager
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

        # Mock existing GlucoseExercise record
        cls.mock_existing_glucose_exercise_record = GlucoseExercise(
            id=5, strava_id=12345, glucose_id=12345
        )

        # Mock strava data
        cls.activity_start = datetime(2000, 1, 1, 12, 0, 0)
        cls.activity_end = datetime(2000, 1, 1, 13, 0, 0)
        cls.mock_strava_data = [
            Strava(
                id=12346,
                distance=10,
                activity_type="WALK",
                start_time=cls.activity_start,
                end_time=cls.activity_end,
            ),
            Strava(
                id=12347,
                distance=10,
                activity_type="WALK",
                start_time=cls.activity_start,
                end_time=cls.activity_end,
            ),
        ]  # Id is bigger than 1 of last record strava id

    @patch("src.database_manager.DatabaseManager")
    def test_get_glucose_records_within_interval(self, mock_database_manager):
        data = DataManager(mock_database_manager)
        # Some data data
        data._get_glucose_records_within_interval(
            datetime(2000, 1, 1), datetime(2000, 2, 1)
        )
        mock_database_manager.get_records_between_timestamp.assert_called_once()
        mock_database_manager.get_records_between_timestamp.assert_called_with(
            Glucose, datetime(2000, 1, 1), datetime(2000, 2, 1)
        )

    @patch("src.database_manager.DatabaseManager")
    def test_combine_data_no_strava_data(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = (
            self.mock_existing_glucose_exercise_record
        )
        mock_database_manager.get_filtered_by_id_records.return_value = (
            []
        )  # Mock get_filtered_by_id_records to be empty
        data = DataManager(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(GlucoseExercise)
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            Strava, 12345
        )
        # No data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 0)

    @patch("src.database_manager.DatabaseManager")
    def test_combine_data_no_libre_data(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = (
            self.mock_existing_glucose_exercise_record
        )

        mock_database_manager.get_filtered_by_id_records.return_value = (
            self.mock_strava_data
        )
        mock_database_manager.get_records_between_timestamp.return_value = (
            []
        )  # Mock glucose data to be empty
        data = DataManager(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(GlucoseExercise)
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            Strava, 12345
        )
        self.assertEqual(
            mock_database_manager.get_records_between_timestamp.call_count, 2
        )
        # No data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 0)

    @patch("src.database_manager.DatabaseManager")
    def test_combine_data_success(self, mock_database_manager):
        mock_database_manager.get_last_record.return_value = (
            self.mock_existing_glucose_exercise_record
        )
        mock_database_manager.get_filtered_by_id_records.return_value = (
            self.mock_strava_data
        )
        mock_database_manager.get_records_between_timestamp.return_value = [
            Glucose(
                id=1, glucose=2, timestamp=self.activity_start + timedelta(seconds=20)
            ),
            Glucose(
                id=2, glucose=6, timestamp=self.activity_start + timedelta(seconds=40)
            ),
        ]  # Mock libre data, can be anything as long as its length 3
        data = DataManager(mock_database_manager)
        # No data
        data.combine_data()
        # Assert mocks
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_with(GlucoseExercise)
        mock_database_manager.get_filtered_by_id_records.assert_called_once()
        mock_database_manager.get_filtered_by_id_records.assert_called_with(
            Strava, 12345
        )
        self.assertEqual(
            mock_database_manager.get_records_between_timestamp.call_count, 2
        )
        # Data saved
        self.assertEqual(mock_database_manager.save_data.call_count, 1)

        # TODO: Figure out why the calls don't match
        # mock_database_manager.save_data.assert_called_with(
        #     ([
        #         GlucoseExercise(
        #             id=6,
        #             timestamp=self.activity_start + timedelta(seconds=20),
        #             activity_type="RUN",
        #             distance=5,
        #             glucose=2,
        #             strava_id=12346,
        #             glucose_id=1,
        #             seconds_since_start=20,
        #             activity_start=self.activity_start,
        #             activity_end=self.activity_end,
        #         ),
        #         GlucoseExercise(
        #             id=7,
        #             glucose=6,
        #             glucose_id=2,
        #             strava_id=12346,
        #             timestamp=self.activity_start + timedelta(seconds=40),
        #             activity_type="RUN",
        #             distance=5,
        #             activity_start=self.activity_start,
        #             activity_end=self.activity_end,
        #             seconds_since_start=40,
        #         ),
        #         GlucoseExercise(
        #             id=8,
        #             glucose_id=1,
        #             glucose=2,
        #             strava_id=12347,
        #             timestamp=self.activity_start + timedelta(seconds=20),
        #             activity_type="WALK",
        #             distance=10,
        #             activity_start=self.activity_start,
        #             activity_end=self.activity_end,
        #             seconds_since_start=20,
        #         ),
        #         GlucoseExercise(
        #             id=9,
        #             glucose=6,
        #             glucose_id=2,
        #             strava_id=12347,
        #             timestamp=self.activity_start + timedelta(seconds=40),
        #             activity_type="WALK",
        #             distance=10,
        #             activity_start=self.activity_start,
        #             activity_end=self.activity_end,
        #             seconds_since_start=40,
        #         ),
        #     ]),
        # )
