import unittest
from unittest import mock

from src.database.tables import Glucose, GlucoseExercise, Strava
from src.database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        super().setUp()

    def test_validate_data_type(self):
        mock_engine = mock.MagicMock()
        database_manager = DatabaseManager(mock_engine)
        # Success
        for model in (Glucose, Strava, GlucoseExercise):
            with self.subTest(model=model):
                database_manager._validate_data_type(model)
        # Raise value Error
        with self.assertRaises(ValueError) as ex:
            database_manager._validate_data_type("model")
        self.assertEqual(str(ex.exception), "Invalid data_type model")

    @mock.patch("src.database_manager.Session")
    def test_save_data(self, mock_session):
        # Establish mocks
        mock_engine = mock.MagicMock()
        database_manager = DatabaseManager(mock_engine)
        session = mock.MagicMock()
        mock_session.return_value.__enter__.return_value = session
        # Success
        database_manager.save_data([])
        session.add_all.assert_called()
        session.add_all.assert_called_with([])
        session.commit.assert_called()
        session.commit.assert_called_with()

    @mock.patch("src.database_manager.Session")
    def test_get_last_record(self, mock_session):
        # Establish mocks
        mock_engine = mock.MagicMock()
        database_manager = DatabaseManager(mock_engine)
        # Not testing defaults so just return a dummy value
        database_manager._get_default_last_record = lambda x: 1
        session_mock = mock.MagicMock()
        execute_mock = mock.MagicMock()
        execute_mock.scalar.return_value = []
        session_mock.execute.return_value = execute_mock
        mock_session.return_value.__enter__.return_value = session_mock

        # Result Not found
        res = database_manager.get_last_record(Glucose)
        session_mock.execute.assert_called_once()
        execute_mock.scalar.assert_called_once()
        self.assertEqual(res, 1)

        # Result Found
        # Do not care on the actual result type just that a result was found
        execute_mock.scalar.return_value = 1
        session_mock.execute.return_value = execute_mock
        mock_session.return_value.__enter__.return_value = session_mock

        res = database_manager.get_last_record(Glucose)
        self.assertEqual(session_mock.execute.call_count, 2)
        self.assertEqual(execute_mock.scalar.call_count, 2)
        self.assertEqual(res, 1)

    @mock.patch("src.database_manager.Session")
    def test_get_records_between_timestamp(self, mock_session):
        # Establish mocks
        mock_engine = mock.MagicMock()
        database_manager = DatabaseManager(mock_engine)

        # Result Not found
        session_mock = mock.MagicMock()
        session_mock.execute.return_value = []
        mock_session.return_value.__enter__.return_value = session_mock
        res = database_manager.get_records_between_timestamp(
            Glucose, "start", "end", "time_column"
        )
        session_mock.execute.assert_called_once()
        self.assertEqual(res, [])

        #  Result Found
        # Do not care on the actual result type
        session_mock.execute.return_value = [(1,), (2,)]
        mock_session.return_value.__enter__.return_value = session_mock
        res = database_manager.get_records_between_timestamp(
            Glucose, "start", "end", "time_column"
        )
        self.assertEqual(session_mock.execute.call_count, 2)
        self.assertEqual(res, [1, 2])

    @mock.patch("src.database_manager.Session")
    def test_get_filtered_by_id_records(self, mock_session):
        # Establish mocks
        mock_engine = mock.MagicMock()
        database_manager = DatabaseManager(mock_engine)

        # Result Not found
        session_mock = mock.MagicMock()
        session_mock.execute.return_value = []
        mock_session.return_value.__enter__.return_value = session_mock
        res = database_manager.get_filtered_by_id_records(Glucose, 2)
        session_mock.execute.assert_called_once()
        self.assertEqual(res, [])

        #  Result Found
        # Do not care on the actual result type
        session_mock.execute.return_value = [(1,), (2,)]
        mock_session.return_value.__enter__.return_value = session_mock
        res = database_manager.get_filtered_by_id_records(Glucose, 2)
        self.assertEqual(session_mock.execute.call_count, 2)
        self.assertEqual(res, [1, 2])
