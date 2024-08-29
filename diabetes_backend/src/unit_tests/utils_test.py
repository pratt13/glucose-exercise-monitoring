import os
import unittest
from unittest.mock import patch
from datetime import datetime as dt

from src.constants import DATABASE_DATETIME, DATETIME_FORMAT, STRAVA_DATETIME
from src.utils import (
    aggregate_glucose_data,
    aggregate_strava_data,
    convert_str_to_ts,
    convert_ts_to_str,
    load_libre_credentials_from_env,
    load_strava_credentials_from_env,
)


TEST_ENV = {
    "LIBRE_EMAIL": "LIBRE_EMAIL",
    "LIBRE_PASSWORD": "LIBRE_PASSWORD",
    "STRAVA_CLIENT_ID": "STRAVA_CLIENT_ID",
    "STRAVA_CLIENT_SECRET": "STRAVA_CLIENT_SECRET",
    "STRAVA_REFRESH_TOKEN": "STRAVA_REFRESH_TOKEN",
    "STRAVA_CODE": "STRAVA_CODE",
}


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.dt = dt(2020, 5, 2, 13, 12, 1)
        self.test_glucose_data = [
            (1, dt(2020, 5, 2, 13, 4, 1), 5),
            (2, dt(2020, 5, 2, 13, 8, 1), 5.5),
            (6, dt(2024, 5, 2, 13, 8, 1), 5.5),  # Different year
            (3, dt(2020, 5, 2, 13, 12, 1), 6),
            (4, dt(2020, 5, 2, 13, 22, 1), 5.2),
            (5, dt(2020, 5, 2, 13, 51, 1), 6),
        ]

    def test_convert_str_to_ts(self):
        self.assertEqual(
            convert_str_to_ts("2020/05/02 13:12:01", "%Y/%m/%d %H:%M:%S"), self.dt
        )
        self.assertEqual(
            convert_str_to_ts("2020-05-02 13:12:01", DATABASE_DATETIME), self.dt
        )
        self.assertEqual(
            convert_str_to_ts("2020-05-02 13:12:01", STRAVA_DATETIME), self.dt
        )
        self.assertEqual(
            convert_str_to_ts("05/02/2020 01:12:01 PM", DATETIME_FORMAT), self.dt
        )

    def test_convert_ts_to_str(self):
        self.assertEqual(
            convert_ts_to_str(self.dt, "%Y/%m/%d %H:%M:%S"), "2020/05/02 13:12:01"
        )
        self.assertEqual(
            convert_ts_to_str(self.dt, DATABASE_DATETIME), "2020-05-02 13:12:01"
        )
        self.assertEqual(
            convert_ts_to_str(self.dt, STRAVA_DATETIME), "2020-05-02 13:12:01"
        )
        self.assertEqual(
            convert_ts_to_str(self.dt, DATETIME_FORMAT), "05/02/2020 01:12:01 PM"
        )

    def test_load_libre_credentials_from_env_no_env(self):
        self.assertEqual(load_libre_credentials_from_env(), (None, None))

    @patch.dict(
        os.environ,
        TEST_ENV,
        clear=True,
    )
    def test_load_libre_credentials_from_env_with_env(self):
        self.assertEqual(
            load_libre_credentials_from_env(), ("LIBRE_EMAIL", "LIBRE_PASSWORD")
        )

    def test_load_strava_credentials_from_env_no_env(self):
        self.assertEqual(load_strava_credentials_from_env(), (None, None, None, None))

    @patch.dict(
        os.environ,
        TEST_ENV,
        clear=True,
    )
    def test_load_strava_credentials_from_env_with_env(self):
        self.assertEqual(
            load_strava_credentials_from_env(),
            (
                "STRAVA_CLIENT_ID",
                "STRAVA_CLIENT_SECRET",
                "STRAVA_REFRESH_TOKEN",
                "STRAVA_CODE",
            ),
        )

    def test_aggregate_glucose_data(self):
        expected_data = {
            "intervals": ["13:00", "13:15", "13:30", "13:45"],
            "mean": [5.5, 5.2, 0, 6],
            "count": [4, 1, 0, 1],
            "median": [5.5, 5.2, 0, 6],
            "var": [0.16666666666666674, 0.0, 0.0, 0.0],
            "raw": [[5.0, 5.5, 5.5, 6.0], [5.2], [], [6.0]],
            "std": [0.40824829046386313, 0.0, 0.0, 0.0],
            "max": [6, 5.2, 0, 6],
            "min": [5, 5.2, 0, 6],
        }
        self.assertEqual(
            aggregate_glucose_data(self.test_glucose_data, 1, 2), expected_data
        )

    def test_aggregate_strava_data(self):
        strava_data = [
            ("Run", 60.1),
            ("Run", 10),
            ("Cycle", 42),
            ("Run", 10),
            ("Run", 10),
            ("Run", 10),
            ("Cycle", 20),
        ]
        expected_data = {
            "activity": ["Cycle", "Run"],
            "total_distance": [
                62,
                100.1,
            ],
            "number_activities": [2, 5],
        }
        self.assertEqual(aggregate_strava_data(strava_data, 1, 0), expected_data)
