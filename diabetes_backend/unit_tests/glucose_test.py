import unittest, os, sys
from unittest.mock import patch, MagicMock
from datetime import datetime as dt

from requests import HTTPError

from diabetes_backend.constants import DATETIME_FORMAT, HEADERS

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)


from diabetes_backend.auth import AuthenticationManagement
from glucose import Glucose

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
class TestGlucose(unittest.TestCase):
    def setUp(self):
        super().setUp()

    # def test_format_cgm_data(self, mock_requests, mock_auth_manager, mock_database_manager):
    #     mock_auth_manager.get_token.return_value = "Fake token"
    #     mock_requests.return_value = MockRequest

    #     glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
    #     # print(mock_auth_manager.call_args)

    @patch("requests.get")
    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_get_patient_ids_success(self, mock_database_manager, mock_auth_manager, mock_requests):
        # Format mocks
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_patient_ids = [{"patientId": "123"}, {"patientId": "456"}]
        mock_requests.return_value = MockRequest(mock_patient_ids)

        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
        patient_ids = glucose.get_patient_ids()
        self.assertEqual(patient_ids, [p.get("patientId") for p in mock_patient_ids])

        # Check the mocks
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            "https://api.libreview.io/llu/connections",
            headers={**HEADERS, "Authorization": f"Bearer {mock_token}"},
        )
        mock_database_manager.assert_called_once()
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.get")
    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_get_patient_ids_failure(self, mock_database_manager, mock_auth_manager, mock_requests):
        mock_patient_ids = [{"patientId": "123"}, {"patientId": "456"}]
        mock_requests.return_value = MockRequest(mock_patient_ids, raise_error=True)
        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)

        with self.assertRaises(HTTPError) as ex:
            glucose.get_patient_ids()
        self.assertEqual(str(ex.exception), ERROR_MSG)
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        mock_database_manager.assert_called_once()
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.get")
    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_get_cgm_data_success(self, mock_database_manager, mock_auth_manager, mock_requests):
        # Format mocks
        mock_data = {
            "graphData": [
                {
                    "FactoryTimestamp": "7/11/2024 3: 22: 43 AM",
                    "Timestamp": "7/11/2024 4: 22: 43 AM",
                    "type": 0,
                    "ValueInMgPerDl": 80,
                    "MeasurementColor": 1,
                    "GlucoseUnits": 0,
                    "Value": 4.4,
                    "isHigh": False,
                    "isLow": False,
                }
            ]
        }
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_requests.return_value = MockRequest(mock_data)

        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
        patient_id = "patient_id_123"
        result = glucose.get_cgm_data(patient_id)
        self.assertEqual(result, {"data": mock_data})

        # Check the mocks
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"https://api.libreview.io/llu/connections/{patient_id}/graph",
            headers={**HEADERS, "Authorization": f"Bearer {mock_token}"},
        )
        mock_database_manager.assert_called_once()
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.get")
    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_get_cgm_data_failure(self, mock_database_manager, mock_auth_manager, mock_requests):
        # Format mocks
        mock_data = {
            "graphData": [
                {
                    "FactoryTimestamp": "7/11/2024 3: 22: 43 AM",
                    "Timestamp": "7/11/2024 4: 22: 43 AM",
                    "type": 0,
                    "ValueInMgPerDl": 80,
                    "MeasurementColor": 1,
                    "GlucoseUnits": 0,
                    "Value": 4.4,
                    "isHigh": False,
                    "isLow": False,
                }
            ]
        }
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_requests.return_value = MockRequest(mock_data, raise_error=True)

        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
        patient_id = "patient_id_123"
        with self.assertRaises(HTTPError) as ex:
            glucose.get_cgm_data(patient_id)
        self.assertEqual(str(ex.exception), ERROR_MSG)
        # Check the mocks
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_auth_manager.return_value.get_token.assert_called_once_with()
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"https://api.libreview.io/llu/connections/{patient_id}/graph",
            headers={**HEADERS, "Authorization": f"Bearer {mock_token}"},
        )
        mock_database_manager.assert_called_once()
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")

    @patch("requests.get")
    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_update_cgm_data_success(self, mock_database_manager, mock_auth_manager, mock_requests):
        # Format mocks
        mock_data = {
            "graphData": [
                {
                    "FactoryTimestamp": "7/11/2024 3:22:43 AM",
                    "Timestamp": "7/11/2024 4:22:43 AM",
                    "type": 0,
                    "ValueInMgPerDl": 80,
                    "MeasurementColor": 1,
                    "GlucoseUnits": 0,
                    "Value": 4.4,
                    "isHigh": False,
                    "isLow": False,
                }
            ]
        }
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_requests.return_value = MockRequest(mock_data)
        mock_database_manager.return_value.get_last_record.return_value = (
            dt.strptime("12/31/2000 10:30:00 AM", DATETIME_FORMAT),
            1,
        )

        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
        patient_id = "patient_id_123"
        result = glucose.update_cgm_data(patient_id)
        self.assertIsNone(result)

        # Check the mocks
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            f"https://api.libreview.io/llu/connections/{patient_id}/graph",
            headers={**HEADERS, "Authorization": f"Bearer {mock_token}"},
        )
        mock_database_manager.assert_called_once()
        mock_database_manager.assert_called_once_with("user", "password", "host", "dbname")
        mock_database_manager.return_value.get_last_record.assert_called_once()
        mock_database_manager.return_value.get_last_record.assert_called_once_with()
        mock_database_manager.return_value.save_glucose_data.assert_called_once()
        mock_database_manager.return_value.save_glucose_data.assert_called_once_with(
            [(2, 4.4, "7/11/2024 4:22:43 AM")]
        )

    @patch("diabetes_backend.auth.AuthenticationManagement", autospec=True)
    @patch("diabetes_backend.database_manager.PostgresManager")
    def test_format_cgm_data(self, mock_database_manager, mock_auth_manager):
        last_timestamp, id = dt.strptime("12/31/2000 10:30:00 AM", DATETIME_FORMAT), 1
        test_data = [
            {"Timestamp": "12/31/2000 10:29:59 AM", "Value": 5.2},
            {"Timestamp": "12/31/2000 10:30:00 AM", "Value": 5.3},
            {"Timestamp": "12/31/2000 10:30:01 AM", "Value": 5.4},
        ]
        glucose = Glucose("email", "password", mock_auth_manager, mock_database_manager)
        result = glucose.format_cgm_data(last_timestamp, id, test_data)
        self.assertEqual(result, [(2, 5.4, "12/31/2000 10:30:01 AM")])
