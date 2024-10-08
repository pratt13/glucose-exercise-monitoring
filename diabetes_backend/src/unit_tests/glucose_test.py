import os
import unittest
from unittest.mock import patch
from datetime import datetime as dt
from datetime import timezone
from requests import HTTPError
from src.unit_tests.base import TestBase
from src.constants import HEADERS
from src.glucose import GlucoseManager
from src.database.tables import Glucose

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
class TestGlucose(TestBase):
    def setUp(self):
        super().setUp()
        self.test_data_1 = {
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
        self.test_data_2 = {
            "FactoryTimestamp": "7/11/2024 3:22:43 AM",
            "Timestamp": "7/11/2024 4:23:43 AM",
            "type": 0,
            "ValueInMgPerDl": 80,
            "MeasurementColor": 1,
            "GlucoseUnits": 0,
            "Value": 4.4,
            "isHigh": False,
            "isLow": False,
        }
        self.test_data_3 = {
            "FactoryTimestamp": "7/11/2024 3:22:43 AM",
            "Timestamp": "7/11/2024 4:24:43 AM",
            "type": 0,
            "ValueInMgPerDl": 80,
            "MeasurementColor": 1,
            "GlucoseUnits": 0,
            "Value": 4.4,
            "isHigh": False,
            "isLow": False,
        }

    @patch("requests.get")
    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_get_patient_ids_success(
        self, mock_database_manager, mock_auth_manager, mock_requests
    ):
        # Format mocks
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_patient_ids = [{"patientId": "123"}, {"patientId": "456"}]
        mock_requests.return_value = MockRequest(mock_patient_ids)

        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )
        patient_ids = glucose.get_patient_ids()
        self.assertEqual(patient_ids, [p.get("patientId") for p in mock_patient_ids])

        # Check the mocks
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        mock_requests.assert_called_once_with(
            "https://api.libreview.io/llu/connections",
            headers={**HEADERS, "Authorization": f"Bearer {mock_token}"},
        )
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_get_patient_ids_failure(
        self, mock_database_manager, mock_auth_manager, mock_requests
    ):
        mock_patient_ids = [{"patientId": "123"}, {"patientId": "456"}]
        mock_requests.return_value = MockRequest(mock_patient_ids, raise_error=True)
        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )

        with self.assertRaises(HTTPError) as ex:
            glucose.get_patient_ids()
        self.assertEqual(str(ex.exception), ERROR_MSG)
        mock_auth_manager.return_value.get_token.assert_called_once()
        mock_requests.assert_called_once()
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_get_cgm_data_success(
        self, mock_database_manager, mock_auth_manager, mock_requests
    ):
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

        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )
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
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_get_cgm_data_failure(
        self, mock_database_manager, mock_auth_manager, mock_requests
    ):
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

        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )
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
        self.assertEqual(mock_database_manager.call_count, 0)

    @patch("requests.get")
    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_update_cgm_data_success(
        self, mock_database_manager, mock_auth_manager, mock_requests
    ):
        # Format mocks
        mock_data = {"graphData": [self.test_data_1]}
        mock_token = "mock_token"
        mock_auth_manager.return_value.get_token.return_value = mock_token
        mock_requests.return_value = MockRequest(mock_data)
        mock_database_manager.get_last_record.return_value = Glucose(
            id=1,
            timestamp=dt(2020, 1, 1, 12, 0, 0).astimezone(timezone.utc),
            glucose=5,
        )

        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )
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
        mock_database_manager.get_last_record.assert_called_once()
        mock_database_manager.get_last_record.assert_called_once_with(Glucose)
        mock_database_manager.save_data.assert_called_once()

    @patch("src.auth.AuthenticationManagement", autospec=True)
    @patch("src.database_manager.DatabaseManager")
    def test_format_cgm_data(self, mock_database_manager, mock_auth_manager):
        id = 1
        last_timestamp = dt(2000, 12, 31, 10, 30).astimezone(timezone.utc)
        test_data = [
            {"Timestamp": "12/31/2000 10:29:59 AM", "Value": 5.2},
            {"Timestamp": "12/31/2000 10:30:00 AM", "Value": 5.3},
            {"Timestamp": "12/31/2000 10:30:01 AM", "Value": 5.4},
        ]
        glucose = GlucoseManager(
            "email", "password", mock_auth_manager, mock_database_manager
        )
        results = glucose.format_cgm_data(last_timestamp, id, test_data)

        self.assertResultRepresentations(
            results, [Glucose(id=2, timestamp="12/31/2000 10:30:01 AM", glucose=5.4)]
        )

        # All records are returned
        results = glucose.format_cgm_data(
            dt(1000, 11, 7).astimezone(timezone.utc),
            0,
            [self.test_data_1, self.test_data_2, self.test_data_3],
        )

        self.assertResultRepresentations(
            results,
            [
                Glucose(
                    id=1,
                    glucose=self.test_data_1.get("Value"),
                    timestamp=self.test_data_1.get("Timestamp"),
                ),
                Glucose(
                    id=2,
                    glucose=self.test_data_2.get("Value"),
                    timestamp=self.test_data_2.get("Timestamp"),
                ),
                Glucose(
                    id=3,
                    glucose=self.test_data_3.get("Value"),
                    timestamp=self.test_data_3.get("Timestamp"),
                ),
            ],
        )

        # Some records are returned
        results = glucose.format_cgm_data(
            dt(2024, 7, 11, 4, 23, 43).astimezone(timezone.utc),
            2,
            [self.test_data_1, self.test_data_2, self.test_data_3],
        )
        self.assertResultRepresentations(
            results,
            [
                Glucose(
                    id=3,
                    glucose=self.test_data_3.get("Value"),
                    timestamp=self.test_data_3.get("Timestamp"),
                )
            ],
        )
