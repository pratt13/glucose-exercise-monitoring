from unittest.mock import patch
from requests import HTTPError
from datetime import datetime
from src.unit_tests.base import TestBase
from src.database.tables import Strava
from src.utils import compute_epoch
from src.constants import STRAVA_BASE_URL
from src.strava import StravaManager

ERROR_MSG = "My test error"


class MockRequest:
    def __init__(self, response, raise_error=False):
        self.response = response
        self.raise_error = raise_error

    def json(self):
        return self.response

    def raise_for_status(self):
        if self.raise_error:
            raise HTTPError(ERROR_MSG)


class TestStrava(TestBase):
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

    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_get_access_token_success(self, mock_database_manager, mock_requests):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests.return_value = MockRequest({"access_token": "token"})
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )
        result = strava_cls.get_access_token()

        self.assertEqual(result, "token")

        # Check the mocks
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_get_access_token_failure(self, mock_database_manager, mock_requests):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests.return_value = MockRequest(
            {"access_token": "token"}, raise_error=True
        )
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )

        with self.assertRaises(HTTPError) as ex:
            strava_cls.get_access_token()
        self.assertEqual(str(ex.exception), ERROR_MSG)

        # Check the mocks
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_get_activity_data_success(
        self, mock_database_manager, mock_requests_post, mock_requests_get
    ):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests_post.return_value = MockRequest({"access_token": "token"})
        mock_requests_get.return_value = MockRequest([self.test_data_1])
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )
        result = strava_cls.get_activity_data()
        self.assertEqual(result, [self.test_data_1])

        # Check the mocks
        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers={"Authorization": "Bearer token"},
            params={},
        )
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_get_activity_data_failure(
        self, mock_database_manager, mock_requests_post, mock_requests_get
    ):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests_post.return_value = MockRequest({"access_token": "token"})
        mock_requests_get.return_value = MockRequest(
            [self.test_data_1], raise_error=True
        )
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )

        with self.assertRaises(HTTPError) as ex:
            strava_cls.get_activity_data()
        self.assertEqual(str(ex.exception), ERROR_MSG)

        # Check the mocks
        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers={"Authorization": "Bearer token"},
            params={},
        )
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("src.database_manager.DatabaseManager")
    def test_format_activity_data(self, mock_database_manager):
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )
        # Simple
        result = strava_cls.format_activity_data(self.test_data_1)
        self.assertResultRepresentation(
            result, Strava(id="1231", elapsed_time=8, activity_type="Run", distance=105)
        )

        # No lat-lang
        result = strava_cls.format_activity_data(
            {**self.test_data_1, "start_latlng": [], "end_latlng": []}
        )
        self.assertResultRepresentation(
            result,
            Strava(
                id="1231",
                start_time=self.start_time,
                end_time=self.end_time,
                elapsed_time=8,
                activity_type="Run",
                distance=105,
                moving_time=6,
                start_latitude=0,
                end_latitude=0,
                start_longitude=0,
                end_longitude=0,
            ),
        )

    @patch("requests.get")
    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_update_data_records_found(
        self, mock_database_manager, mock_requests_post, mock_requests_get
    ):
        mock_dt = datetime(2000, 1, 1)
        mock_database_manager.get_last_record.return_value = Strava(
            start_time=mock_dt, distance=5, activity_type="RUN"
        )
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests_post.return_value = MockRequest({"access_token": "token"})
        mock_requests_get.return_value = MockRequest([self.test_data_1])
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )
        self.assertIsNone(strava_cls.update_data())

        # Check the mocks
        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers={"Authorization": "Bearer token"},
            params={"page": 1, "records_per_page": 1, "after": compute_epoch(mock_dt)},
        )
        mock_database_manager.get_last_record.assert_called_once_with(Strava)
        self.assertEqual(mock_database_manager.save_data.call_count, 1)

    @patch("requests.get")
    @patch("requests.post")
    @patch("src.database_manager.DatabaseManager")
    def test_update_data_records_non_found(
        self, mock_database_manager, mock_requests_post, mock_requests_get
    ):
        mock_dt = datetime(2000, 1, 1, 12, 0, 0)
        mock_database_manager.get_last_record.return_value = Strava(
            start_time=mock_dt, activity_type="WALK", distance=10
        )
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests_post.return_value = MockRequest({"access_token": "token"})
        mock_requests_get.return_value = MockRequest([])
        strava_cls = StravaManager(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.code,
            mock_database_manager,
        )
        self.assertIsNone(strava_cls.update_data())

        # Check the mocks
        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers={"Authorization": "Bearer token"},
            params={"page": 1, "records_per_page": 1, "after": compute_epoch(mock_dt)},
        )
        mock_database_manager.get_last_record.assert_called_once_with(Strava)
        self.assertEqual(mock_database_manager.save_data.call_count, 0)
