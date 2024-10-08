import unittest
from unittest.mock import call, patch

from src.crons import data_cron, strava_cron, libre_cron


class TestCrons(unittest.TestCase):
    @patch("src.glucose.Glucose")
    def test_cron_no_patients(self, mock_libre):
        mock_libre.get_patient_ids.return_value = []

        libre_cron(mock_libre)

        # Check calls
        mock_libre.get_patient_ids.assert_called_once_with()
        mock_libre.update_cgm_data.assert_not_called()

        # Exception
        mock_libre.get_patient_ids.side_effect = Exception("error")
        libre_cron(mock_libre)
        mock_libre.update_cgm_data.assert_not_called()

    @patch("src.glucose.Glucose")
    def test_cron_many_patients(self, mock_libre):
        patient_ids = ["1", "2"]
        mock_libre.get_patient_ids.return_value = patient_ids

        libre_cron(mock_libre)

        # Check calls
        mock_libre.get_patient_ids.assert_called_once_with()
        calls = [call(patient_id) for patient_id in patient_ids]
        mock_libre.update_cgm_data.assert_has_calls(calls)

        # Exception
        mock_libre.update_cgm_data.side_effect = Exception("error")
        libre_cron(mock_libre)
        self.assertEqual(mock_libre.update_cgm_data.call_count, 3)

    @patch("src.strava.Strava")
    def test_strava_cron(self, mock_strava):
        strava_cron(mock_strava)
        mock_strava.update_data.assert_called_once_with(records_per_page=100, page=1)

        # Exception
        mock_strava.update_data.side_effect = Exception("error")
        strava_cron(mock_strava)
        self.assertEqual(mock_strava.update_data.call_count, 2)

    @patch("src.data.DataManager")
    def test_data_cron(self, mock_data):
        data_cron(mock_data)
        mock_data.combine_data.assert_called_once()
        mock_data.combine_data.assert_called_once_with()

        # Exception
        mock_data.combine_data.side_effect = Exception("error")
        data_cron(mock_data)
        self.assertEqual(mock_data.combine_data.call_count, 2)
