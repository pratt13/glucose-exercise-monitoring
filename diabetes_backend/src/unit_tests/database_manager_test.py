import sys, os, unittest
from unittest import mock
from datetime import datetime as dt
from psycopg2 import sql

# Mangle the paths in tests not in the code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import PostgresManager
from constants import DATA_TYPES, DATETIME_FORMAT, DATABASE_TABLE
EXAMPLE_DATA = [
    [dt.strptime("12/31/2000 10:30:00 AM", DATETIME_FORMAT), 1],
    [dt.strptime("12/31/2000 10:20:00 AM", DATETIME_FORMAT), 2],
    [dt.strptime("12/31/2000 10:10:00 AM", DATETIME_FORMAT), 3],
    [dt.strptime("12/31/2000 10:00:00 AM", DATETIME_FORMAT), 4],
    [dt.strptime("12/31/2000 09:30:00 AM", DATETIME_FORMAT), 5],
]


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.conn_values = {
            "user": "user",
            "password": "password",
            "host": "host",
            "dbname": "dbname",
        }
        self.PostgresManager = PostgresManager(*self.conn_values.values())

    @mock.patch("psycopg2.connect")
    def test_get_last_record(self, mock_connect):
        for data_type, query_str in zip([DATA_TYPES.LIBRE, DATA_TYPES.STRAVA], 
                             ("SELECT timestamp, id FROM glucose_times ORDER BY timestamp DESC LIMIT 1",
                              "SELECT timestamp FROM activtities ORDER BY timestamp DESC LIMIT 1")):
            with self.subTest(data_type=data_type, query_str=query_str):
                mock_con = mock_connect.return_value  # result of psycopg2.connect(**connection_stuff)
                mock_cur = mock_con.cursor.return_value.__enter__.return_value  # result of con.cursor()
                mock_cur.fetchone.return_value = EXAMPLE_DATA[0]  # return this when calling cur.fetchone()

                result = self.PostgresManager.get_last_record()

                self.assertEqual(result, EXAMPLE_DATA[0])

                # Check the calls are as expected
                mock_connect.assert_called_with(**self.conn_values)
                mock_con.cursor.asset_called_with()
                mock_cur.execute.assert_called_once()
                mock_cur.execute.assert_called_with(query_str
                )

    @mock.patch("psycopg2.connect")
    def test_data(self, mock_connect):
        test_data = [
            (1, 4.5, dt(1990, 7, 11, 19, 45, 55)),
            (2, 4.5, dt(1990, 7, 11, 19, 45, 55)),
        ]
        mock_con = mock_connect.return_value  # result of psycopg2.connect(**connection_stuff)
        mock_cur = mock_con.cursor.return_value.__enter__.return_value  # result of con.cursor()

        self.PostgresManager.save_glucose_data(test_data)

        # Check the calls are as expected
        mock_connect.assert_called_with(**self.conn_values)
        mock_con.cursor.asset_called_with()
        mock_cur.executemany.assert_called_once()
        mock_cur.executemany.assert_called_with(
            "INSERT INTO glucose_times (id, glucose, timestamp) VALUES (%s, %s, %s)", test_data
        )
