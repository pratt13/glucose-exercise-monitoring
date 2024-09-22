import os
import unittest
from unittest.mock import patch
from datetime import datetime as dt

from src.constants import DATABASE_DATETIME, DATETIME_FORMAT, STRAVA_DATETIME
from src.utils import (
    aggregate_glucose_data,
    aggregate_strava_data,
    compute_percentages,
    compute_x_time_value,
    compute_y_value_with_x_time,
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

    def test_compute_y_value_with_x_time(self):
        # Two points 2 minutes apart
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 1, 12, 12, 30), 9)

        self.assertEqual(
            compute_y_value_with_x_time(pos1, pos2, 1), [dt(2024, 1, 1, 12, 11, 30), 7]
        )

        # Two points a day apart negative gradient
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 9)
        pos2 = (dt(2024, 1, 2, 12, 10, 30), 5)
        self.assertEqual(
            compute_y_value_with_x_time(pos1, pos2, 12 * 60),
            [dt(2024, 1, 2, 0, 10, 30), 7],
        )

        # Two points a day apart zero gradient
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 2, 12, 10, 30), 5)
        self.assertEqual(
            compute_y_value_with_x_time(pos1, pos2, 12 * 60),
            [dt(2024, 1, 2, 0, 10, 30), 5],
        )

        # Two points, the first placed before the second
        pos1 = (dt(2024, 1, 2, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 1, 12, 10, 30), 6)
        with self.assertRaises(ValueError) as ex:
            compute_y_value_with_x_time(pos1, pos2, 5)
        self.assertEqual(
            str(ex.exception),
            f"Cannot have the second point {pos2[0]} before the first {pos1[0]}",
        )

    def test_compute_x_time_value(self):
        # Two points 20 seconds apart
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 1, 12, 10, 50), 9)
        self.assertEqual(
            compute_x_time_value(pos1, pos2, 7), dt(2024, 1, 1, 12, 10, 40)
        )

        # Two points a day apart negative gradient
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 9)
        pos2 = (dt(2024, 1, 2, 12, 10, 30), 5)
        self.assertEqual(compute_x_time_value(pos1, pos2, 7), dt(2024, 1, 2, 0, 10, 30))

        # Two points a day apart zero gradient
        pos1 = (dt(2024, 1, 1, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 2, 12, 10, 30), 5)
        with self.assertRaises(ValueError) as ex:
            compute_x_time_value(pos1, pos2, 5)
        self.assertEqual(
            str(ex.exception),
            "Cannot compute the time that the y value 5 is reached if the gradient is zero",
        )

        # Two points, the first placed before the second
        pos1 = (dt(2024, 1, 2, 12, 10, 30), 5)
        pos2 = (dt(2024, 1, 1, 12, 10, 30), 6)
        with self.assertRaises(ValueError) as ex:
            compute_x_time_value(pos1, pos2, 5.5)
        self.assertEqual(
            str(ex.exception),
            f"Cannot have the second point {pos2[0]} before the first {pos1[0]}",
        )

    def test_compute_percentages(self):
        # High is less than low
        with self.assertRaises(ValueError) as ex:
            compute_percentages([], high=4.5, low=4.5)
        self.assertEqual(
            str(ex.exception), "Cannot specify the high value 4.5 <= low value 4.5"
        )

        test_result_1 = {
            "percentageOfTimeInTarget": None,
            "percentageOfTimeLow": None,
            "percentageOfTimeHigh": None,
            "numberOfHighs": None,
            "numberOfLows": None,
        }
        # No data
        self.assertEqual(compute_percentages([]), test_result_1)

        # Single data
        # In target
        self.assertEqual(
            compute_percentages([("12:00", 6)]),
            {
                "percentageOfTimeInTarget": 100,
                "percentageOfTimeLow": 0,
                "percentageOfTimeHigh": 0,
                "numberOfHighs": 0,
                "numberOfLows": 0,
            },
        )
        # High
        self.assertEqual(
            compute_percentages([("12:00", 9.2)], high=9),
            {
                "percentageOfTimeInTarget": 0,
                "percentageOfTimeLow": 0,
                "percentageOfTimeHigh": 100,
                "numberOfHighs": 1,
                "numberOfLows": 0,
            },
        )
        # Low
        self.assertEqual(
            compute_percentages([("12:00", 4.9)], low=5),
            {
                "percentageOfTimeInTarget": 0,
                "percentageOfTimeLow": 100,
                "percentageOfTimeHigh": 0,
                "numberOfHighs": 0,
                "numberOfLows": 1,
            },
        )

        ## TODO: More complicated tests for data > 1

        # Data across 20 minutes
        data = [
            (dt(2024, 1, 1, 12, 0, 00), 5),
            (dt(2024, 1, 1, 12, 4, 00), 5),  # 4 minutes in target, 20% in target
            (dt(2024, 1, 1, 12, 6, 00), 7),  # 2 minute increment, 10% in target
            (
                dt(2024, 1, 1, 12, 10, 00),
                11,
            ),  # 1 minute high (5%), 3 minutes in target (17.5%)
            (
                dt(2024, 1, 1, 12, 12, 00),
                7,
            ),  # 1/2 minute high (2.5%), 1.5 minutes in target (7.5%)
            (
                dt(2024, 1, 1, 12, 14, 00),
                3,
            ),  # 3/2 minute in target (7.5%) 1/2 minute low (2.5%)
            (dt(2024, 1, 1, 12, 16, 00), 3),  # 2 minutes low (10%)
            (
                dt(2024, 1, 1, 12, 18, 00),
                5,
            ),  # 1 minute low (5%) 1 minute in target (5%)
            (
                dt(2024, 1, 1, 12, 20, 00),
                3,
            ),  # 1 minute low (5%) 1 minute in target (5%)
        ]
        self.assertEqual(
            compute_percentages(data, interval_length_seconds=20 * 60, low=4, high=10),
            {
                "percentageOfTimeInTarget": 70,
                "percentageOfTimeLow": 22.5,
                "percentageOfTimeHigh": 7.5,
                "numberOfHighs": 1,
                "numberOfLows": 2,
            },
        )
