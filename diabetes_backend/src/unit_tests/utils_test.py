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
    get_seconds_from_pandas_interval,
    glucose_quartile_data,
    group_glucose_data_by_day,
    libre_hba1c,
    load_libre_credentials_from_env,
    load_strava_credentials_from_env,
    populate_glucose_data,
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
            "q10": [5.15, 5.2, 0.0, 6.0],
            "q25": [5.375, 5.2, 0.0, 6.0],
            "q75": [5.625, 5.2, 0.0, 6.0],
            "q90": [5.85, 5.2, 0.0, 6.0],
        }
        self.assertDictEqual(
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

    def test_libre_hba1c(self):
        # No data
        self.assertEqual(libre_hba1c([], 1, 0), {"hBA1C": None})
        self.assertEqual(libre_hba1c([(1, 2)], 1, 0), {"hBA1C": None})

        # Data range is too small
        data = [(5, dt(2000, 1, 1, 12, 0, 0)), (5, dt(2000, 1, 1, 12, 12, 0))]
        self.assertEqual(libre_hba1c(data, 1, 0), {"hBA1C": None})

        # Valid data
        data = [
            (6, dt(2000, 1, 1, 12, 0, 0)),
            (6, dt(2000, 1, 1, 12, 10, 0)),  # 10 minutes mean 6
            (8, dt(2000, 1, 1, 12, 30, 0)),  # 20 mins mean 7
            (12, dt(2000, 1, 1, 12, 40, 0)),  # 10 mins mean 10
            (2, dt(2000, 1, 1, 13, 10, 0)),  # 30 mins mean 7
            (4, dt(2000, 1, 1, 13, 30, 0)),  # 20 mins mean 3
        ]
        # 90 minutes
        # (10 * 6 + 20 * 7 + 10 * 10 + 30 * 7 + 20 * 3) / 90 = 6.33333333333
        self.assertEqual(libre_hba1c(data, 1, 0), {"hBA1C": 6.333333333333333})

    def test_get_seconds_from_pandas_interval(self):
        self.assertEqual(get_seconds_from_pandas_interval("10min"), 600)
        self.assertEqual(get_seconds_from_pandas_interval("90min"), 90 * 60)
        with self.assertRaises(NotImplementedError):
            get_seconds_from_pandas_interval("1hour")

    def test_glucose_quartile_data(self):
        data = [
            # First quarter day 1
            (6, dt(2000, 1, 1, 12, 1, 0)),
            (7, dt(2000, 1, 1, 12, 10, 0)),
            (8, dt(2000, 1, 1, 12, 14, 0)),
            # Second quarter day 1
            (8, dt(2000, 1, 1, 12, 20, 0)),
            (7, dt(2000, 1, 1, 12, 29, 0)),
            # Third quarter day 1
            (6, dt(2000, 1, 1, 12, 35, 0)),
            (6, dt(2000, 1, 1, 12, 40, 0)),
            (5, dt(2000, 1, 1, 12, 44, 0)),
            # Second day, quarter 1
            (12, dt(2000, 1, 2, 12, 1, 0)),
            (14, dt(2000, 1, 2, 12, 10, 0)),
            (15, dt(2000, 1, 2, 12, 14, 0)),
            # No data in second quarter
            # Third quarter day 2
            (5, dt(2000, 1, 2, 12, 35, 0)),
            (3, dt(2000, 1, 2, 12, 40, 0)),
            (4, dt(2000, 1, 2, 12, 44, 0)),
        ]
        self.assertEqual(
            glucose_quartile_data(data, 1, 0),
            {
                "intervals": ["12:00", "12:15", "12:30"],
                "count": [6, 2, 6],
                "maxValues": [15.0, 8.0, 6.0],
                "minValues": [6.0, 7.0, 3.0],
                "medianValues": [10.0, 7.5, 5.0],
                "q10": [6.5, 7.1, 3.5],
                "q25": [7.25, 7.25, 4.25],
                "q75": [13.5, 7.75, 5.75],
                "q90": [14.5, 7.9, 6.0],
            },
        )

    def test_populate_glucose_data(self):
        # Unequal lists
        with self.assertRaises(ValueError) as ex:
            populate_glucose_data([1], [])
        self.assertEqual(
            str(ex.exception),
            "Cannot have different length timestamp (1) and glucose lists (0)",
        )

        # List to short lists
        with self.assertRaises(ValueError) as ex:
            populate_glucose_data([1], [2])
        self.assertEqual(
            str(ex.exception),
            "Not enough data: (1)",
        )

        # Populate an hour data with the boundary points
        # No data point at first boundary point, only after
        # no data between 30 and 45 minutes
        # Data is designed so on the interval it is nice and easy
        timestamp_data = [
            dt(2024, 1, 1, 12, 5, 0),
            dt(2024, 1, 1, 12, 10, 0),
            dt(2024, 1, 1, 12, 20, 0),
            dt(2024, 1, 1, 12, 25, 0),
            dt(2024, 1, 1, 12, 50, 0),
            dt(2024, 1, 1, 12, 55, 0),
        ]
        glucose_data = [6, 8, 10, 12, 8, 7]
        expected_new_data = [
            (dt(2024, 1, 1, 12, 14, 59), 9.0),
            (dt(2024, 1, 1, 12, 15, 0), 9.0),
            (dt(2024, 1, 1, 12, 29, 59), 11.2),
            (dt(2024, 1, 1, 12, 30, 0), 11.2),
            (dt(2024, 1, 1, 12, 44, 59), 8.8),
            (dt(2024, 1, 1, 12, 45, 0), 8.8),
        ]
        expected_timestamp_data, expected_glucose_data = list(
            zip(
                *sorted(
                    expected_new_data + list(zip(timestamp_data, glucose_data)),
                    key=lambda x: x[0],
                )
            )
        )
        res_timestamp_data, res_glucose_data = populate_glucose_data(
            timestamp_data, glucose_data, interval_in_mins=15
        )
        self.assertEqual(expected_timestamp_data, res_timestamp_data)
        self.assertEqual(expected_glucose_data, res_glucose_data)

    def test_group_glucose_data_by_day(self):
        data = [
            # Day 2
            (dt(2024, 1, 2, 12, 5, 0), 10),
            (dt(2024, 1, 2, 12, 15, 0), 10),
            (dt(2024, 1, 2, 13, 30, 0), 11),
            # Day 1
            (dt(2024, 1, 1, 12, 5, 0), 9),
            (dt(2024, 1, 1, 12, 15, 0), 10),
            (dt(2024, 1, 1, 13, 30, 0), 11),
            # Day 3
            (dt(2024, 1, 3, 12, 5, 0), 9),
            (dt(2024, 1, 3, 12, 15, 0), 10),
            (dt(2024, 1, 3, 13, 30, 0), 12),
        ]
        # Test unsorted, unsorted and string glucose data
        for test_data, is_sorted, is_glucose_string in zip(
            (
                data,
                sorted(data, key=lambda x: x[0]),
                list(map(lambda x: (x[0], str(x[1])), data)),
            ),
            [False, True, False],
            [False, False, True],
        ):
            with self.subTest(is_sorted=is_sorted, is_glucose_string=is_glucose_string):
                self.assertDictEqual(
                    group_glucose_data_by_day(test_data, 0, 1),
                    {
                        "2024-01-01": [
                            ("12:05:00", 9.0),
                            ("12:15:00", 10.0),
                            ("13:30:00", 11.0),
                        ],
                        "2024-01-02": [
                            ("12:05:00", 10.0),
                            ("12:15:00", 10.0),
                            ("13:30:00", 11.0),
                        ],
                        "2024-01-03": [
                            ("12:05:00", 9.0),
                            ("12:15:00", 10.0),
                            ("13:30:00", 12.0),
                        ],
                    },
                )
