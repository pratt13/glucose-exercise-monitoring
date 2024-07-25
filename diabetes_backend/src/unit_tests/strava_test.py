import unittest, os, sys
from unittest.mock import patch
from datetime import datetime as dt
from requests import HTTPError


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import DATA_TYPES, DATETIME_FORMAT, HEADERS, STRAVA_BASE_URL
from glucose import Glucose
from strava import Strava

ERROR_MSG = "My test error"


class MockRequest:
    def __init__(self, token, raise_error=False):
        self.token = token
        self.raise_error = raise_error

    def json(self):
        return {"access_token": self.token}

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
class TestStrava(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.client_id = "myId"
        self.client_secret = "secret"
        self.refresh_token = "my_token"
        # Test data sample - we skip some records for brevity
        self.test_data_1 = {
            "id": "1",
            "athlete": {"id": "123"},
            "distance": 105,
            "type": "Run",
            "moving_time": 5.6,
            "elapsed_time": 6.2,
            "start_date": 1,
            "start_latlng": [4.4, 6.2],
            "end_latlng": [5.5, 7.1],
        }

    @patch("requests.post")
    @patch("database_manager.PostgresManager")
    def test_get_token_success(self, mock_database_manager, mock_requests):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests.return_value = MockRequest("token")
        strava_cls = Strava(
            self.client_id, self.client_secret, self.refresh_token, mock_database_manager
        )
        result = strava_cls.get_token()

        self.assertEqual(result, "token")

        # Check the mocks
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        self.assertEqual(mock_database_manager.call_count, 1)
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.post")
    @patch("database_manager.PostgresManager")
    def test_get_token_failure(self, mock_database_manager, mock_requests):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "f": "json",
        }
        mock_requests.return_value = MockRequest("token", raise_error=True)
        strava_cls = Strava(
            self.client_id, self.client_secret, self.refresh_token, mock_database_manager
        )

        with self.assertRaises(HTTPError) as ex:
            strava_cls.get_token()
        self.assertEqual(str(ex.exception), ERROR_MSG)

        # Check the mocks
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        self.assertEqual(mock_database_manager.call_count, 1)
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.get")
    @patch("requests.post")
    @patch("database_manager.PostgresManager")
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
        mock_requests_post.return_value = MockRequest("token")
        mock_requests_get.return_value = MockRequest(self.test_data_1)
        strava_cls = Strava(
            self.client_id, self.client_secret, self.refresh_token, mock_database_manager
        )
        result = strava_cls.get_token()
        self.assertEqual(result, "token")

        # Check the mocks
        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
        )
        mock_requests_get.assert_called_once()
        mock_requests_post.assert_called_once_with(
            f"{STRAVA_BASE_URL}/api/v3/athlete/activities",
            headers={"Authorization": f"Authorization: Bearer token"},
            params={},
        )
        self.assertEqual(mock_database_manager.call_count, 1)
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    # @patch("requests.post")
    # @patch("database_manager.PostgresManager")
    # def test_get_token_failure(self, mock_database_manager, mock_requests):
    #     payload = {
    #         "client_id": self.client_id,
    #         "client_secret": self.client_secret,
    #         "refresh_token": self.refresh_token,
    #         "grant_type": "refresh_token",
    #         "f": "json",
    #     }
    #     mock_requests.return_value = MockRequest("token", raise_error=True)
    #     strava_cls = Strava(
    #         self.client_id, self.client_secret, self.refresh_token, mock_database_manager
    #     )

    #     with self.assertRaises(HTTPError) as ex:
    #         strava_cls.get_token()
    #     self.assertEqual(str(ex.exception), ERROR_MSG)

    #     # Check the mocks
    #     mock_requests.assert_called_once()
    #     mock_requests.assert_called_once_with(
    #         f"{STRAVA_BASE_URL}/oauth/token", data=payload, verify=False
    #     )
    #     self.assertEqual(mock_database_manager.call_count, 1)
    #     mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("database_manager.PostgresManager")
    def test_format_activity_data(self, mock_database_manager):
        strava_cls = Strava(
            self.client_id, self.client_secret, self.refresh_token, mock_database_manager
        )
        result = strava_cls.format_activity_data(self.test_data_1)

        self.assertDictEqual(
            result,
            {
                "id": "1231",
                "distance": 105,
                "activity_type": "Run",
                "moving_time": 5.6,
                "elapsed_time": 6.2,
                "start_time": 1,
                "end_time": 1,
                "start_latitude": 4.4,
                "end_latitude": 5.5,
                "start_longitude": 6.2,
                "end_longitude": 7.1,
            },
        )
