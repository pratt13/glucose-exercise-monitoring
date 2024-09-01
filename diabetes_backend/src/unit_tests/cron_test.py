import unittest
from unittest.mock import call, patch

from src.crons import data_cron, strava_cron, libre_cron


class TestCrons(unittest.TestCase):
    @patch("glucose.Glucose")
    def test_cron_no_patients(self, mock_libre):
        mock_libre.get_patient_ids.return_value = []

        libre_cron(mock_libre)

        # Check calls
        mock_libre.get_patient_ids.assert_called_once_with()
        mock_libre.update_cgm_data.assert_not_called()

    @patch("glucose.Glucose")
    def test_cron_many_patients(self, mock_libre):
        patient_ids = ["1", "2"]
        mock_libre.get_patient_ids.return_value = patient_ids

        libre_cron(mock_libre)

        # Check calls
        mock_libre.get_patient_ids.assert_called_once_with()
        calls = [call(patient_id) for patient_id in patient_ids]
        mock_libre.update_cgm_data.assert_has_calls(calls)

    @patch("strava.Strava")
    def test_strava_cron(self, mock_strava):
        strava_cron(mock_strava)
        mock_strava.update_data.assert_called_once_with(records_per_page=100, page=1)

    @patch("data.Data")
    def test_(self, mock_data):
        data_cron(mock_data)
        mock_data.combine_data.assert_called_once()
        mock_data.combine_data.assert_called_once_with()
