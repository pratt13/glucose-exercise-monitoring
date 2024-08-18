import os
import unittest
from unittest.mock import patch
from datetime import datetime as dt

from src.constants import DATABASE_DATETIME, DATETIME_FORMAT, STRAVA_DATETIME
from src.utils import (
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
}


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.dt = dt(2020, 5, 2, 13, 12, 1)

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
        self.assertEqual(load_strava_credentials_from_env(), (None, None, None))

    @patch.dict(
        os.environ,
        TEST_ENV,
        clear=True,
    )
    def test_load_strava_credentials_from_env_with_env(self):
        self.assertEqual(
            load_strava_credentials_from_env(),
            ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"),
        )
